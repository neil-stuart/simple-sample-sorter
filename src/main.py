import curses
import panes
from widgets import (w_explr,
                    w_wlist,
                    w_prompt_quit,
                    w_hlist,
                    w_prompt_return,
                    w_vflist,
                    w_prompt_hdelete,
                    w_alert,
                    w_dir_select)
import w_id
import names

WIDTH = 75
HEADER_H, MAIN_H, FOOTER_H = [2,45,5]


def main(stdscr):
    curses.noecho(), curses.cbreak(), curses.curs_set(0)
    stdscr.clear(), stdscr.keypad(True)

    header_pane = panes.header_pane(HEADER_H,WIDTH,0)
    main_pane = panes.main_pane(MAIN_H,WIDTH,HEADER_H)
    footer_pane = panes.footer_pane(FOOTER_H,WIDTH,HEADER_H+MAIN_H)

    main_pane.widget_list = create_widgets(main_pane)
    main_pane.actv_wdgt = main_pane.get_wdgt(w_id.MAIN_MENU)

    while not main_pane.quit:

        footer_pane.controls = main_pane.actv_wdgt.controls
        header_pane.title = main_pane.actv_wdgt.label

        inp = main_pane.getch()

        header_pane.char = inp

        main_pane.input(inp)

    else:
        pass

def create_widgets(main_pane):

    alert = w_alert(main_pane, names.LB_ALERT, w_id.ALERT)

    vfile_list = w_vflist(main_pane, names.LB_VFILES, w_id.VFILE_EXPLR)

    menu_list = w_wlist(main_pane, names.LB_MAIN_MENU, w_id.MAIN_MENU)

    hier_list = w_hlist(main_pane, names.LB_LOAD_HIER, w_id.HIER_LIST)

    quit_prompt = w_prompt_quit(main_pane, names.LB_QUIT, w_id.QUIT)

    return_prompt = w_prompt_return(main_pane, names.LB_RETURN, w_id.EXIT)

    del_hier_prompt = w_prompt_hdelete(main_pane, names.LB_QUIT, w_id.DEL_HIER)

    file_explr = w_explr(main_pane, names.LB_EXPLORER, w_id.EXPLORER)

    dir_select = w_dir_select(main_pane, names.LB_DIR_SLCT, w_id.DIR_SELECT, file_explr)

    quit_prompt.parent = menu_list
    menu_list.add([hier_list, quit_prompt])

    return [
        menu_list, # Main Menu List.
        hier_list, # Load Hierarchy list.
        vfile_list, # Virtual File list
        quit_prompt, # Quit Prompt
        return_prompt,
        del_hier_prompt,
        alert,
        file_explr,
        dir_select
    ]



if __name__=="__main__":
    curses.wrapper(main)

