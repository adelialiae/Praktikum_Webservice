# Aktifkan lingkungan kerja webservicep2plending
# Jalankan server menggunakan uvicorn dengan file utama "main" dan objek FastAPI "app" yang diaktifkan ulang secara otomatis saat terjadi perubahan
from typing import Union
from fastapi import FastAPI,Response,Request,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Tambahkan middleware CORS untuk mengizinkan CORS (Cross-Origin Resource Sharing)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],            # Izinkan akses dari semua origin
	allow_credentials=True,        # Izinkan mengirim kredensial saat permintaan cross-origin
	allow_methods=["*"],           # Izinkan semua metode HTTP (GET, POST, dll.)
	allow_headers=["*"],           # Izinkan semua header HTTP
)

# Definisi endpoint dan fungsi handler untuk endpoint "/"
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Definisi endpoint dan fungsi handler untuk endpoint "/mahasiswa/{nim}"
@app.get("/mahasiswa/{nim}")
def ambil_mhs(nim:str):
    return {"nama": "Budi Martami"}

# Definisi endpoint dan fungsi handler untuk endpoint "/mahasiswa2/"
@app.get("/mahasiswa2/")
def ambil_mhs2(nim:str):
    return {"nama": "Budi Martami 2"}

# Definisi endpoint dan fungsi handler untuk endpoint "/daftar_mhs/"
@app.get("/daftar_mhs/")
def daftar_mhs(id_prov:str,angkatan:str):
    return {"query":" idprov: {}  ; angkatan: {} ".format(id_prov,angkatan),"data":[{"nim":"1234"},{"nim":"1235"}]}

# Endpoint untuk inisialisasi database (hanya dipanggil sekali)
@app.get("/init/")
def init_db():
  try:
    DB_NAME = "upi.db"
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    # Query untuk membuat tabel 'mahasiswa' jika belum ada
    create_table = """ CREATE TABLE mahasiswa(
            ID      	INTEGER PRIMARY KEY 	AUTOINCREMENT,
            nim     	TEXT            	NOT NULL,
            nama    	TEXT            	NOT NULL,
            id_prov 	TEXT            	NOT NULL,
            angkatan	TEXT            	NOT NULL,
            tinggi_badan  INTEGER
        )  
        """
    cur.execute(create_table)
    con.commit
  except:
           return ({"status":"terjadi error"})  # Tangani kesalahan jika terjadi
  finally:
           con.close()
    
  return ({"status":"ok, db dan tabel berhasil dicreate"})  # Berhasil membuat database dan tabel

# Impor BaseModel dari modul pydantic dan Optional dari modul typing
from pydantic import BaseModel
from typing import Optional

# Definisikan model data untuk Mahasiswa
class Mhs(BaseModel):
   nim: str
   nama: str
   id_prov: str
   angkatan: str
   tinggi_badan: Optional[int] | None = None  # Tinggi badan bisa null

# Endpoint untuk menambahkan data mahasiswa (metode POST)
@app.post("/tambah_mhs/", response_model=Mhs,status_code=201)  
def tambah_mhs(m: Mhs,response: Response, request: Request):
   try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       # Query untuk menambahkan data mahasiswa ke tabel
       cur.execute("""insert into mahasiswa (nim,nama,id_prov,angkatan,tinggi_badan) values ( "{}","{}","{}","{}",{})""".format
                   (m.nim,m.nama,m.id_prov,m.angkatan,m.tinggi_badan))
       con.commit() 
   except:
       print("oioi error")
       return ({"status":"terjadi error"})   
   finally:  	 
       con.close()
   response.headers["Location"] = "/mahasiswa/{}".format(m.nim) 
   print(m.nim)
   print(m.nama)
   print(m.angkatan)
  
   return m

# Endpoint untuk menampilkan semua data mahasiswa (metode GET)
@app.get("/tampilkan_semua_mhs/")
def tampil_semua_mhs():
   try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       recs = []
       # Query untuk mengambil semua data mahasiswa dari tabel
       for row in cur.execute("select * from mahasiswa"):
           recs.append(row)
   except:
       return ({"status":"terjadi error"})   
   finally:  	 
       con.close()
   return {"data":recs}

# Impor jsonable_encoder dari fastapi.encoders
from fastapi.encoders import jsonable_encoder

# Endpoint untuk memperbarui data mahasiswa menggunakan metode PUT
@app.put("/update_mhs_put/{nim}",response_model=Mhs)
def update_mhs_put(response: Response,nim: str, m: Mhs ):
    # Update seluruh data mahasiswa
    # Karena kunci 'nim' tidak diubah
    try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       # Query untuk memeriksa apakah data mahasiswa ada
       cur.execute("select * from mahasiswa where nim = ?", (nim,) )
       existing_item = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))   
    
    if existing_item:  # Data ditemukan 
            print(m.tinggi_badan)
            # Query untuk memperbarui data mahasiswa
            cur.execute("update mahasiswa set nama = ?, id_prov = ?, angkatan=?, tinggi_badan=? where nim=?", 
                        (m.nama,m.id_prov,m.angkatan,m.tinggi_badan,nim))
            con.commit()            
            response.headers["location"] = "/mahasiswa/{}".format(m.nim)
    else:  # Data tidak ditemukan
            print("item not foud")
            raise HTTPException(status_code=404, detail="Item Not Found")
      
    con.close()
    return m

# Definisikan model data untuk patch (perubahan parsial)
class MhsPatch(BaseModel):
   nama: str | None = "kosong"
   id_prov: str | None = "kosong"
   angkatan: str | None = "kosong"
   tinggi_badan: Optional[int] | None = -9999  # Hanya tinggi badan yang bisa null

# Endpoint untuk memperbarui data mahasiswa menggunakan metode PATCH
@app.patch("/update_mhs_patch/{nim}", response_model=MhsPatch)
def update_mhs_patch(response: Response, nim: str, m: MhsPatch):
    try:
        # Cetak data yang diterima untuk debugging
        print(str(m))
        
        # Nama database
        DB_NAME = "upi.db"
        
        # Koneksi ke database
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor() 

        # Query untuk memeriksa apakah data mahasiswa dengan nim tertentu ada dalam database
        cur.execute("select * from mahasiswa where nim = ?", (nim,))
        existing_item = cur.fetchone()
    except Exception as e:
        # Tangani kesalahan jika terjadi exception saat mengakses database
        raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))  
    
    if existing_item:  # Data ditemukan, lakukan update
        sqlstr = "update mahasiswa set "  # Asumsikan minimal ada satu field yang diperbarui

        # Proses pembentukan query SQL untuk melakukan pembaruan data pada tabel mahasiswa berdasarkan perubahan yang diberikan
        if m.nama != "kosong":
            if m.nama is not None:
                sqlstr = sqlstr + " nama = '{}' ,".format(m.nama)
            else:
                sqlstr = sqlstr + " nama = null ,"

        if m.angkatan != "kosong":
            if m.angkatan is not None:
                sqlstr = sqlstr + " angkatan = '{}' ,".format(m.angkatan)
            else:
                sqlstr = sqlstr + " angkatan = null ,"

        if m.id_prov != "kosong":
            if m.id_prov is not None:
                sqlstr = sqlstr + " id_prov = '{}' ,".format(m.id_prov)
            else:
                sqlstr = sqlstr + " id_prov = null, "

        if m.tinggi_badan != -9999:
            if m.tinggi_badan is not None:
                sqlstr = sqlstr + " tinggi_badan = {} ,".format(m.tinggi_badan)
            else:
                sqlstr = sqlstr + " tinggi_badan = null ,"

        sqlstr = sqlstr[:-1] + " where nim='{}' ".format(nim)  # Buang koma terakhir
        print(sqlstr)

        try:
            # Eksekusi query untuk melakukan pembaruan data
            cur.execute(sqlstr)
            con.commit()

            # Set header location untuk menunjukkan URL mahasiswa yang diperbarui
            response.headers["location"] = "/mahasixswa/{}".format(nim)
        except Exception as e:
            # Tangani kesalahan jika terjadi exception saat menjalankan query SQL
            raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))
    else:  # Data tidak ditemukan, 404 - item not found
        raise HTTPException(status_code=404, detail="Item Not Found")

    # Tutup koneksi database
    con.close()
    
    # Kembalikan data mahasiswa yang diperbarui
    return m

  
# Endpoint untuk menghapus data mahasiswa menggunakan metode DELETE
@app.delete("/delete_mhs/{nim}")
def delete_mhs(nim: str):
    try:
       DB_NAME = "upi.db"
       con = sqlite3.connect(DB_NAME)
       cur = con.cursor()
       # Query untuk menghapus data mahasiswa berdasarkan nim
       sqlstr = "delete from mahasiswa  where nim='{}'".format(nim)                 
       print(sqlstr) # debug 
       cur.execute(sqlstr)
       con.commit()
    except:
       return ({"status":"terjadi error"})   
    finally:  	 
       con.close()
    
    return {"status":"ok"}
