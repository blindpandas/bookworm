use libc::c_int;
use std::mem::size_of;
use windows::Win32::Foundation::{HWND, LPARAM, WPARAM};
use windows::Win32::UI::Controls::RichEdit::{
    CFE_LINK, CFM_LINK, CHARFORMATW, CHARRANGE, EM_EXGETSEL, EM_EXSETSEL, EM_GETEVENTMASK,
    EM_SETCHARFORMAT, EM_SETEVENTMASK, ENM_SELCHANGE, EN_SELCHANGE, SCF_SELECTION, SELCHANGE,
    SEL_EMPTY,
};
use windows::Win32::UI::Controls::NMHDR;
use windows::Win32::UI::WindowsAndMessaging::SendMessageW;

type Position = c_int;

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
        cbSize: u32::try_from(size_of::<CHARFORMATW>()).unwrap(),
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
