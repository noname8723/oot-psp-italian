#!/usr/bin/env python3
from pathlib import Path
import struct
import hashlib
import sys

# ---- File attesi nella stessa cartella di questo script ----
CLEAN_ROM = Path('baserom.z64')               # OoT USA NTSC 1.0 limpia
ITALIAN_ROM = Path('oot-ntsc-1.0.z64')        # ROM già tradotta in italiano (oppure creata da una patch .ips)
EBOOT = Path('EBOOT.PBP')
ASSETS = Path('oot_psp_assets.bin')
OUT_DIR = Path('output_it')

# ---- Constantes del port/build que subiste ----
DMADATA_OFF = 0x7430
DMADATA_COUNT = 1510
MESSAGE_TABLE_OFF_IN_CODE = 0xF98AC

# VROM originales NTSC 1.0
VROM_NES_FONT = 0x00928000
VROM_NES_MESSAGES = 0x0092D000
VROM_JPN_MESSAGES = 0x008EB000

# Slots dentro de oot_psp_assets.bin, según tu EBOOT/port
PSP_JPN_MSG_FILE_OFF = 0x008D72B0
PSP_JPN_MSG_VROM = 0x208D72B0
PSP_JPN_MSG_CAPACITY = 0x003A350

PSP_NES_FONT_FILE_OFF = 0x00912800
PSP_NES_FONT_SIZE = 0x00004580

PSP_OLD_NES_MSG_VROM = 0x20916D80
PSP_OLD_NES_MSG_FILE_OFF = 0x00916D80
PSP_OLD_NES_MSG_SIZE = 0x00038130

EXPECTED_CLEAN_MD5 = '5bd1fe107bf8106b2ab6650abecd54d6'
EXPECTED_ASSETS_SIZE = 0x03267B10
EXPECTED_MSG_COUNT = 2115  # sin el 0xFFFF final; incluye 0xFFFD


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def be32(b: bytes, off: int) -> int:
    return struct.unpack_from('>I', b, off)[0]


def parse_dmadata(rom: bytes):
    out = []
    for i in range(DMADATA_COUNT):
        off = DMADATA_OFF + i * 16
        if off + 16 > len(rom):
            break
        vs, ve, rs, re = struct.unpack_from('>IIII', rom, off)
        out.append((vs, ve, rs, re))
    return out


def yaz0_decompress(src: bytes, expected_size: int) -> bytes:
    if src[:4] != b'Yaz0':
        raise ValueError('Il blocco non è Yaz0')
    if be32(src, 4) != expected_size:
        raise ValueError('Dimensione Yaz0 inattesa')

    pos = 16
    out = bytearray()
    code = 0
    bits_left = 0

    while len(out) < expected_size:
        if bits_left == 0:
            if pos >= len(src):
                raise ValueError('Yaz0 troncato')
            code = src[pos]
            pos += 1
            bits_left = 8

        if code & 0x80:
            if pos >= len(src):
                raise ValueError('Yaz0 troncato')
            out.append(src[pos])
            pos += 1
        else:
            if pos + 1 >= len(src):
                raise ValueError('Yaz0 troncato')
            b1, b2 = src[pos], src[pos + 1]
            pos += 2
            distance = ((b1 & 0x0F) << 8) | b2
            length = b1 >> 4
            if length == 0:
                if pos >= len(src):
                    raise ValueError('Yaz0 troncato')
                length = src[pos] + 0x12
                pos += 1
            else:
                length += 2

            copy_pos = len(out) - distance - 1
            if copy_pos < 0:
                raise ValueError('Riferimento Yaz0 non valido')
            for _ in range(length):
                out.append(out[copy_pos])
                copy_pos += 1
                if len(out) == expected_size:
                    break

        code = (code << 1) & 0xFF
        bits_left -= 1

    return bytes(out)


def load_dma_asset(rom: bytes, entry) -> bytes:
    vs, ve, rs, re = entry
    size = ve - vs
    if size <= 0:
        raise ValueError('Voce DMA vuota')
    if re == 0:
        if rs + size > len(rom):
            raise ValueError('Dato DMA fuori dalla ROM')
        return rom[rs:rs + size]

    if re > len(rom) or rs >= re:
        raise ValueError('Voce DMA compressa non valida')
    stored = rom[rs:re]
    if stored[:4] == b'Yaz0':
        return yaz0_decompress(stored, size)
    raise ValueError('Compressione sconosciuta in un dato DMA')


def find_dma_by_vrom(entries, vrom_start: int):
    for e in entries:
        if e[0] == vrom_start:
            return e
    raise ValueError(f'VROM 0x{vrom_start:08X} non trovata nella dmadata (la ROM italiana non è una NTSC 1.0 compatibile?)')


def find_code_blob(rom: bytes, entries) -> bytes:
    # El code de esta versión mide ~1 MiB. En vez de confiar en el índice,
    # comprobamos la firma real de la tabla japonesa en 0xF98AC.
    signature = bytes.fromhex('00 01 23 00 08 00 00 00 00 02 23 00 08 00 00 6C')
    for e in entries:
        size = e[1] - e[0]
        if not (0x100000 <= size <= 0x110000):
            continue
        try:
            data = load_dma_asset(rom, e)
        except Exception:
            continue
        if len(data) >= MESSAGE_TABLE_OFF_IN_CODE + len(signature):
            if data[MESSAGE_TABLE_OFF_IN_CODE:MESSAGE_TABLE_OFF_IN_CODE + len(signature)] == signature:
                return data
    raise ValueError('Impossibile trovare il file code / la tabella dei messaggi nella ROM italiana')


def parse_message_table(code: bytes):
    pos = MESSAGE_TABLE_OFF_IN_CODE

    # En NTSC vienen primero los mensajes japoneses hasta 0xFFFF.
    while True:
        if pos + 8 > len(code):
            raise ValueError('Tabella giapponese troncata')
        text_id, type_pos, pad, ptr = struct.unpack_from('>HBBI', code, pos)
        pos += 8
        if text_id == 0xFFFF:
            break

    english = []
    while True:
        if pos + 8 > len(code):
            raise ValueError('Tabella inglese/italiana troncata')
        text_id, type_pos, pad, ptr = struct.unpack_from('>HBBI', code, pos)
        pos += 8
        if text_id == 0xFFFF:
            break
        if (ptr >> 24) != 0x07:
            raise ValueError(f'Puntatore anomalo nel messaggio 0x{text_id:04X}: 0x{ptr:08X}')
        english.append((text_id, type_pos, ptr & 0x00FFFFFF))

    if len(english) != EXPECTED_MSG_COUNT:
        raise ValueError(f'Attesi {EXPECTED_MSG_COUNT} messaggi, trovati {len(english)} (la patch cambia la struttura dei messaggi)')
    if english[0][0] != 0x0001 or english[-1][0] != 0xFFFD:
        raise ValueError('La tabella dei messaggi non ha la forma attesa')
    return english


def reverse_8byte_blocks(data: bytes) -> bytes:
    if len(data) % 8 != 0:
        raise ValueError('Il font non è allineato a 8 byte')
    out = bytearray(len(data))
    for i in range(0, len(data), 8):
        out[i:i+8] = data[i:i+8][::-1]
    return bytes(out)


def build_psp_message_table(entries, bank_size: int) -> bytes:
    out = bytearray()
    for i, (text_id, type_pos, start_off) in enumerate(entries):
        if i + 1 < len(entries):
            end_off = entries[i + 1][2]
        else:
            end_off = bank_size

        if not (0 <= start_off <= end_off <= bank_size):
            raise ValueError(
                f'Offset non validi nel messaggio 0x{text_id:04X}: '
                f'0x{start_off:X}..0x{end_off:X} / 0x{bank_size:X}'
            )

        out += struct.pack(
            '<HBBII',
            text_id,
            type_pos,
            0,
            PSP_JPN_MSG_VROM + start_off,
            PSP_JPN_MSG_VROM + end_off,
        )
    return bytes(out)


def find_psp_nes_table(eboot: bytes) -> int:
    # Firma de la tabla inglesa original del EBOOT que subiste.
    signature = (
        struct.pack('<I', EXPECTED_MSG_COUNT) +
        struct.pack('<HBBII', 0x0001, 0x23, 0, 0x20916D80, 0x20916E04) +
        struct.pack('<HBBII', 0x0002, 0x23, 0, 0x20916E04, 0x20916E70)
    )
    hits = []
    start = 0
    while True:
        p = eboot.find(signature, start)
        if p < 0:
            break
        hits.append(p)
        start = p + 1
    if len(hits) != 1:
        raise ValueError(f'Impossibile identificare in modo univoco la tabella PSP nell\'EBOOT (corrispondenze: {len(hits)}): EBOOT non compatibile o già modificato')
    return hits[0] + 4  # saltar el contador u32


def verify_external_asset_layout(eboot: bytes):
    # Comprobamos que este EBOOT usa exactamente los slots que vamos a tocar.
    jpn_desc = struct.pack(
        '<IIIIII',
        0x208D72B0, 0x20911600,
        0x008EB000, 0x00925350,
        0x00000000, 0x008D72B0,
    )
    font_desc = struct.pack(
        '<IIIIII',
        0x20912800, 0x20916D80,
        0x00928000, 0x0092C580,
        0x00000003, 0x00912800,
    )
    if eboot.find(jpn_desc) < 0:
        raise ValueError('L\'EBOOT non ha il descrittore atteso di jpn_message_data_static (versione del port diversa?)')
    if eboot.find(font_desc) < 0:
        raise ValueError('L\'EBOOT non ha il descrittore atteso di nes_font_static (versione del port diversa?)')


def apply_ips(rom: bytes, ips: bytes) -> bytes:
    """Applica una patch IPS (anche formato EOF/RLE) a una ROM."""
    if ips[:5] != b'PATCH':
        raise ValueError('Il file .ips non ha l\'intestazione PATCH')
    out = bytearray(rom)
    pos = 5
    while True:
        if pos + 3 > len(ips):
            raise ValueError('IPS troncato')
        if ips[pos:pos + 3] == b'EOF':
            pos += 3
            if pos + 3 <= len(ips):  # estensione: dimensione finale
                size = int.from_bytes(ips[pos:pos + 3], 'big')
                if size < len(out):
                    del out[size:]
            break
        off = int.from_bytes(ips[pos:pos + 3], 'big')
        size = int.from_bytes(ips[pos + 3:pos + 5], 'big')
        pos += 5
        if size == 0:
            rle = int.from_bytes(ips[pos:pos + 2], 'big')
            val = ips[pos + 2:pos + 3]
            pos += 3
            data = val * rle
        else:
            data = ips[pos:pos + size]
            pos += size
        if off + len(data) > len(out):
            out.extend(bytes(off + len(data) - len(out)))
        out[off:off + len(data)] = data
    return bytes(out)


def load_italian_rom(clean: bytes) -> bytes:
    if ITALIAN_ROM.is_file():
        return ITALIAN_ROM.read_bytes()
    ips_files = sorted(Path('.').glob('*.ips')) + sorted(Path('.').glob('*.IPS'))
    if ips_files:
        print(f'Applico la patch {ips_files[0]} alla ROM pulita...')
        rom = apply_ips(clean, ips_files[0].read_bytes())
        ITALIAN_ROM.write_bytes(rom)
        print(f'Creata {ITALIAN_ROM} (MD5 {md5(rom)})')
        return rom
    raise ValueError('Manca oot-ntsc-1.0.z64 oppure un file .ips da applicare')


def main():
    for p in (CLEAN_ROM, EBOOT, ASSETS):
        if not p.is_file():
            print(f'ERRORE: manca {p}')
            print('Metti baserom.z64, EBOOT.PBP, oot_psp_assets.bin e la patch .ips (o la ROM italiana) in questa cartella.')
            return 1

    clean = CLEAN_ROM.read_bytes()
    italian = load_italian_rom(clean)
    eboot = bytearray(EBOOT.read_bytes())
    assets = bytearray(ASSETS.read_bytes())

    print('== Verifica dei file ==')
    print(f'ROM pulita MD5:   {md5(clean)}')
    print(f'ROM italiana MD5: {md5(italian)}')
    print(f'EBOOT MD5:        {md5(eboot)}')
    print(f'Assets MD5:       {md5(assets)}')

    if md5(clean) != EXPECTED_CLEAN_MD5:
        raise ValueError('baserom.z64 non è la ROM USA NTSC 1.0 pulita attesa (MD5 5bd1fe107bf8106b2ab6650abecd54d6)')
    if len(assets) != EXPECTED_ASSETS_SIZE:
        raise ValueError(
            f'oot_psp_assets.bin ha dimensione 0x{len(assets):X}; '
            f'attesa 0x{EXPECTED_ASSETS_SIZE:X}: file di un altro build del port, o già modificato'
        )

    verify_external_asset_layout(eboot)

    clean_dma = parse_dmadata(clean)
    ita_dma = parse_dmadata(italian)

    # --- Extraer banco español de diálogos ---
    ita_msg_entry = find_dma_by_vrom(ita_dma, VROM_NES_MESSAGES)
    ita_messages = load_dma_asset(italian, ita_msg_entry)
    print(f'Banco italiano:   0x{len(ita_messages):X} bytes')
    if len(ita_messages) > PSP_JPN_MSG_CAPACITY:
        raise ValueError('Il banco italiano non entra nello spazio previsto nel file assets')

    # Verificar que el pack original realmente contiene el banco inglés limpio
    clean_msg_entry = find_dma_by_vrom(clean_dma, VROM_NES_MESSAGES)
    clean_messages = load_dma_asset(clean, clean_msg_entry)
    packed_old = bytes(assets[PSP_OLD_NES_MSG_FILE_OFF:PSP_OLD_NES_MSG_FILE_OFF + len(clean_messages)])
    if packed_old != clean_messages:
        raise ValueError('Il blocco inglese nel file assets non coincide con la ROM pulita: assets già modificato o non originale. Interrotto per sicurezza')

    # --- Extraer y convertir font español ---
    clean_font = load_dma_asset(clean, find_dma_by_vrom(clean_dma, VROM_NES_FONT))
    ita_font = load_dma_asset(italian, find_dma_by_vrom(ita_dma, VROM_NES_FONT))
    if len(clean_font) != PSP_NES_FONT_SIZE or len(ita_font) != PSP_NES_FONT_SIZE:
        raise ValueError('Dimensione inattesa di nes_font_static')

    # En este port, nes_font_static se convierte invirtiendo cada palabra de 8 bytes.
    # Lo verificamos contra el asset pack antes de aplicar la misma conversión al font español.
    expected_clean_psp_font = reverse_8byte_blocks(clean_font)
    actual_clean_psp_font = bytes(assets[PSP_NES_FONT_FILE_OFF:PSP_NES_FONT_FILE_OFF + PSP_NES_FONT_SIZE])
    if expected_clean_psp_font != actual_clean_psp_font:
        raise ValueError('La conversione del font non coincide con questo build del port: interrotto per sicurezza')
    ita_font_psp = reverse_8byte_blocks(ita_font)

    # --- Leer la tabla española desde code ---
    ita_code = find_code_blob(italian, ita_dma)
    ita_entries = parse_message_table(ita_code)
    new_psp_table = build_psp_message_table(ita_entries, len(ita_messages))

    # --- Localizar y verificar tabla PSP original ---
    table_off = find_psp_nes_table(eboot)
    print(f'Tabella PSP NES:  0x{table_off:X} dentro EBOOT.PBP')
    old_table_size = EXPECTED_MSG_COUNT * 12
    old_table = bytes(eboot[table_off:table_off + old_table_size])

    # Comprobar que IDs/order coinciden antes de sobrescribir.
    for i, (text_id, _, _) in enumerate(ita_entries):
        old_id = struct.unpack_from('<H', old_table, i * 12)[0]
        if old_id != text_id:
            raise ValueError(
                f'Ordine dei messaggi incompatibile alla voce {i}: '
                f'EBOOT=0x{old_id:04X}, ROM ES=0x{text_id:04X}'
            )

    # --- Aplicar parches ---
    # 1) Guardamos el banco ES dentro del slot japonés, que es más grande.
    assets[PSP_JPN_MSG_FILE_OFF:PSP_JPN_MSG_FILE_OFF + len(ita_messages)] = ita_messages

    # 2) Font castellano ya convertido al formato PSP.
    assets[PSP_NES_FONT_FILE_OFF:PSP_NES_FONT_FILE_OFF + PSP_NES_FONT_SIZE] = ita_font_psp

    # 3) La tabla NES del EBOOT ahora apunta al banco ES alojado en el slot japonés.
    eboot[table_off:table_off + len(new_psp_table)] = new_psp_table

    # --- Verificaciones finales ---
    if len(assets) != EXPECTED_ASSETS_SIZE:
        raise AssertionError('La dimensione del file assets è cambiata: non dovrebbe succedere')
    if len(new_psp_table) != old_table_size:
        raise AssertionError('La tabella PSP ha cambiato dimensione')

    # Confirmar que el primer/último puntero quedan dentro del slot japonés.
    first = struct.unpack_from('<HBBII', new_psp_table, 0)
    last = struct.unpack_from('<HBBII', new_psp_table, len(new_psp_table) - 12)
    if first[3] != PSP_JPN_MSG_VROM:
        raise AssertionError('Il primo messaggio non punta al banco italiano')
    if last[4] != PSP_JPN_MSG_VROM + len(ita_messages):
        raise AssertionError('L\'ultimo messaggio non termina alla fine del banco italiano')

    OUT_DIR.mkdir(exist_ok=True)
    out_eboot = OUT_DIR / 'EBOOT.PBP'
    out_assets = OUT_DIR / 'oot_psp_assets.bin'
    out_eboot.write_bytes(eboot)
    out_assets.write_bytes(assets)

    print('\n== FATTO ==')
    print(f'Creato: {out_eboot}')
    print(f'Creato: {out_assets}')
    print(f'Nuovo EBOOT MD5:  {md5(eboot)}')
    print(f'Nuovo Assets MD5: {md5(assets)}')
    print('\nCopia SOLO questi due file nel port:')
    print('  EBOOT.PBP -> cartella principale del port')
    print('  oot_psp_assets.bin -> data/segments/ del port')
    print('\nNON cancellare oot_psp_assets.bin: se lo cancelli il port lo ricostruisce in inglese.')
    print('Tieni una copia dei file originali per poter tornare indietro.')
    return 0


def _pausa():
    try:
        input('\nPremi Invio per chiudere...')
    except Exception:
        pass


if __name__ == '__main__':
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # lavora nella cartella dello script
    try:
        code = main()
        _pausa()
        sys.exit(code)
    except Exception as exc:
        print(f'\nERRORE: {exc}')
        print('I file originali non sono stati modificati; lo script scrive solo in output_it alla fine.')
        _pausa()
        sys.exit(1)
