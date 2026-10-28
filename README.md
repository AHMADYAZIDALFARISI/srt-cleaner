# srt-cleaner

Membersihkan file subtitle SRT. Membuang tag HTML, keterangan seperti
`[MUSIK]`, label pembicara, baris duplikat, dan memperbaiki waktu yang
tumpang tindih. Satu perintah, tanpa dependensi, tanpa internet.

## Kenapa tool ini ada

File SRT hasil unduhan jarang bersih. Biasanya isinya campuran tag
`<i>`, keterangan bunyi, nama pembicara di depan kalimat, dan baris yang
muncul dua kali. Membersihkannya satu per satu di editor teks itu
pekerjaan yang membosankan dan gampang kelewat. Tool yang sudah ada
umumnya hanya menangani satu jenis kotoran, atau berupa aplikasi web.

## Instalasi

```sh
pip install .
```

Butuh Python 3.9+. Tidak ada dependensi lain. Setelah instalasi, perintah
yang tersedia adalah `srtclean`. Tanpa instalasi pun bisa:
`python -m srtclean berkas.srt`.

## Pakai

```sh
srtclean video.srt
# menulis video.clean.srt dan mencetak ringkasan ke stderr

srtclean video.srt -o bersih.srt --report
srtclean video.srt --in-place   # timpa file asli
srtclean video.srt --dry-run    # hanya laporan, tidak menulis file
```

## Aturan pembersihan

- Tag HTML (`<i>`, `<font ...>`) dan tag gaya ASS (`{...}`) dibuang.
  Entitas HTML (`&amp;` dan sejenisnya) diurai.
- Segmen `[dalam kurung siku]` dibuang. Menurut konvensi subtitle, itu
  deskripsi non-dialog: bunyi, musik, keterangan suasana.
- Baris yang seluruhnya ada di dalam `(tanda kurung)` dibuang dengan
  alasan yang sama. Tanda kurung di tengah kalimat dialog dipertahankan.
- Label pembicara di awal baris (`BUDI: Halo`) dibuang kalau prefiksnya
  huruf kapital atau angka, minimal 2 karakter. `Halo: apa kabar` tidak
  dibuang, karena itu bukan label.
- Cue yang kosong setelah dibersihkan dibuang.
- Cue berurutan yang teksnya persis sama digabung, ujungnya mengikuti
  cue yang paling akhir.
- Waktu diperbaiki: diurutkan, durasi nol atau negatif dijadikan
  1000 ms, tumpang tindih dipangkas dari cue sebelumnya.
- Hasil ditulis ulang dengan penomoran berurutan, encoding UTF-8,
  disertai ringkasan: berapa cue dibuang, digabung, dan diperbaiki.

Tiap langkah bisa dimatikan: `--keep-tags`, `--keep-brackets`,
`--keep-labels`, `--no-dedup`, `--no-timing`.

Kode keluar: `0` kalau berhasil, `2` kalau file tidak bisa dibaca atau
ditulis, atau formatnya rusak (blok tanpa baris waktu yang valid).

## Contoh

File `sample/messy.srt` di repo ini sengaja dibuat kotor (tag, label,
duplikat, waktu tumpang tindih, cue kosong). Menjalankannya:

```sh
srtclean sample/messy.srt --dry-run
```

menghasilkan:

```
Cue: 5 -> 3 (kosong dibuang: 1, digabung: 1, waktu diperbaiki: 1, tag HTML: 2, deskripsi [...]: 2, baris (...): 1, label pembicara: 2)
```

## Keterbatasan

- Tool ini tidak menerjemahkan dan tidak memeriksa ejaan. Isi dialog
  tidak diubah, hanya unsur non-dialog yang dibuang.
- Tidak memperbaiki kesalahan OCR atau sinkronisasi dari audio. Itu
  butuh mendengarkan ulang rekamannya.
- Aturan kurung mengikuti konvensi umum subtitle. Kalau filemu memakai
  kurung untuk dialog sungguhan, pakai `--keep-brackets`.

## Lisensi

MIT, lihat `LICENSE`.
