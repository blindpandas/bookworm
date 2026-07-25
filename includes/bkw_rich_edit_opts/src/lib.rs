use libc::c_int;
use std::{mem::size_of, slice};
use windows::Win32::Foundation::{HWND, LPARAM, WPARAM};
use windows::Win32::UI::Controls::RichEdit::{
    CFE_BOLD, CFE_LINK, CFM_BOLD, CFM_CHARSET, CFM_FACE, CFM_LINK, CFM_SIZE, CHARFORMATW,
    CHARRANGE, EM_EXGETSEL, EM_EXSETSEL, EM_GETEVENTMASK, EM_SETCHARFORMAT, EM_SETEVENTMASK,
    ENM_SELCHANGE, EN_SELCHANGE, SCF_ALL, SCF_DEFAULT, SCF_SELECTION, SELCHANGE, SEL_EMPTY,
};
use windows::Win32::UI::Controls::NMHDR;
use windows::Win32::UI::WindowsAndMessaging::SendMessageW;

type Position = c_int;
const MAX_FACE_NAME_CODE_UNITS: usize = 31;
// wx.FontInfo().FaceName(...) uses these LOGFONT defaults on Windows.
const DEFAULT_CHARSET: u8 = 1;
const DEFAULT_PITCH_AND_FAMILY: u8 = 32;

fn send_character_format(handle: isize, scope: u32, chr_format: &mut CHARFORMATW) -> i32 {
    let result = unsafe {
        SendMessageW(
            HWND(handle),
            EM_SETCHARFORMAT,
            WPARAM(scope as usize),
            LPARAM(chr_format as *mut CHARFORMATW as isize),
        )
    };
    i32::from(result.0 != 0)
}

fn point_size_to_twips(point_size: c_int) -> Option<c_int> {
    if point_size <= 0 {
        return None;
    }
    point_size.checked_mul(20)
}

fn set_text_font(
    handle: isize,
    face_utf16: *const u16,
    face_length: u32,
    point_size: c_int,
    bold: c_int,
    scope: u32,
) -> i32 {
    let face_length = face_length as usize;
    let Some(height) = point_size_to_twips(point_size) else {
        return -1;
    };
    if handle == 0
        || face_utf16.is_null()
        || face_length == 0
        || face_length > MAX_FACE_NAME_CODE_UNITS
        || !matches!(bold, 0 | 1)
    {
        return -1;
    }
    let face = unsafe { slice::from_raw_parts(face_utf16, face_length) };
    if face.contains(&0) {
        return -1;
    }
    let mut chr_format = CHARFORMATW {
        cbSize: size_of::<CHARFORMATW>() as u32,
        // Supplying the charset lets RichEdit bind fallback fonts for glyphs
        // that are not present in the configured face.
        dwMask: CFM_FACE | CFM_SIZE | CFM_BOLD | CFM_CHARSET,
        dwEffects: if bold == 1 {
            CFE_BOLD
        } else {
            Default::default()
        },
        yHeight: height,
        bCharSet: DEFAULT_CHARSET,
        bPitchAndFamily: DEFAULT_PITCH_AND_FAMILY,
        ..Default::default()
    };
    chr_format.szFaceName[..face_length].copy_from_slice(face);
    send_character_format(handle, scope, &mut chr_format)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_SetAllTextFont(
    handle: isize,
    face_utf16: *const u16,
    face_length: u32,
    point_size: c_int,
    bold: c_int,
) -> i32 {
    set_text_font(handle, face_utf16, face_length, point_size, bold, SCF_ALL)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_SetDefaultTextFont(
    handle: isize,
    face_utf16: *const u16,
    face_length: u32,
    point_size: c_int,
    bold: c_int,
) -> i32 {
    set_text_font(
        handle,
        face_utf16,
        face_length,
        point_size,
        bold,
        SCF_DEFAULT,
    )
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_SetAllTextPointSize(handle: isize, point_size: c_int) -> i32 {
    let Some(height) = point_size_to_twips(point_size) else {
        return -1;
    };
    if handle == 0 {
        return -1;
    }
    let mut chr_format = CHARFORMATW {
        cbSize: size_of::<CHARFORMATW>() as u32,
        dwMask: CFM_SIZE,
        yHeight: height,
        ..Default::default()
    };
    send_character_format(handle, SCF_ALL, &mut chr_format)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_FormatRangeAsLink(
    handle: isize,
    start_pos: Position,
    end_pos: Position,
) -> i32 {
    let mut current_chr_range: CHARRANGE = CHARRANGE::default();
    let mut link_chr_range: CHARRANGE = CHARRANGE {
        cpMin: start_pos,
        cpMax: end_pos,
    };
    let mut chr_format: CHARFORMATW = CHARFORMATW {
        cbSize: size_of::<CHARFORMATW>() as u32,
        dwMask: CFM_LINK,
        dwEffects: CFE_LINK,
        ..Default::default()
    };
    let lres = unsafe {
        SendMessageW(
            HWND(handle),
            EM_EXGETSEL,
            WPARAM::default(),
            LPARAM(&mut current_chr_range as *mut CHARRANGE as isize),
        );
        SendMessageW(
            HWND(handle),
            EM_EXSETSEL,
            WPARAM::default(),
            LPARAM(&mut link_chr_range as *mut CHARRANGE as isize),
        );
        let retval = SendMessageW(
            HWND(handle),
            EM_SETCHARFORMAT,
            WPARAM(SCF_SELECTION as usize),
            LPARAM(&mut chr_format as *mut CHARFORMATW as isize),
        );
        SendMessageW(
            HWND(handle),
            EM_EXSETSEL,
            WPARAM::default(),
            LPARAM(&mut current_chr_range as *mut CHARRANGE as isize),
        );
        retval
    };
    if lres.0 == 0 {
        0
    } else {
        1
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_GetNewSelPos(pt_lparam: isize) -> i32 {
    let nmhdr_code = unsafe {
        let nmhdr: &NMHDR = &*(pt_lparam as *const NMHDR);
        (*nmhdr).code
    };
    match nmhdr_code {
        EN_SELCHANGE => unsafe {
            let selchange: &SELCHANGE = &*(pt_lparam as *const SELCHANGE);
            match (*selchange).seltyp {
                SEL_EMPTY => (*selchange).chrg.cpMax,
                _ => -1,
            }
        },
        _ => -1,
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn Bkw_InitCaretTracking(handle: isize) -> i32 {
    let old_mask = unsafe {
        SendMessageW(
            HWND(handle),
            EM_GETEVENTMASK,
            WPARAM::default(),
            LPARAM::default(),
        )
    };
    let new_mask = unsafe {
        SendMessageW(
            HWND(handle),
            EM_SETEVENTMASK,
            WPARAM::default(),
            LPARAM(old_mask.0 | ENM_SELCHANGE as isize),
        )
    };
    if new_mask == old_mask {
        0
    } else {
        1
    }
}
