set nocompatible              " be iMproved, required
filetype off                  " required

" ===== RUNTIME PATH TO INCLUDE VUNDLE AND INITIALIZE =====
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()


" ===== PLUGINS VUNDLE =====
Plugin 'VundleVim/Vundle.vim'
Plugin 'tpope/vim-fugitive'								              "git tools, diff it's nice!
Plugin 'rstacruz/sparkup', {'rtp': 'vim/'}				      "A parser for a condensed HTML format
Plugin 'scrooloose/nerdtree'							              "Files tree
Plugin 'Xuyuanp/nerdtree-git-plugin'                    "show git icons on tree
Plugin 'git://github.com/airblade/vim-gitgutter.git'    "show git icons on code
Plugin 'https://github.com/ctrlpvim/ctrlp.vim'          "buscador de archivos
Plugin 'scrooloose/nerdcommenter'                       "for comment code (don't work yet!)
Plugin 'majutsushi/tagbar'                              "show functions, import, etc.
Plugin 'sickill/vim-monokai'                            "color scheme by monokai
Plugin 'terryma/vim-multiple-cursors'                   "multiple cursors
Plugin 'vim-airline/vim-airline'                        "state bar
Plugin 'vim-airline/vim-airline-themes'                 "themes for state bar
Plugin 'Valloric/YouCompleteMe'                         "complete some codes
Plugin 'honza/vim-snippets'
Plugin 'kannokanno/previm'                              "show .md in real time
Plugin 'ntpeters/vim-better-whitespace'                 "remove whitespaces
Plugin 'NLKNguyen/papercolor-theme'                     "great color scheme
Plugin 'matze/vim-move'                                 "Move in visual mode
Plugin 'hail2u/vim-css3-syntax'                         "Syntaxis de css, less, sass, stylus
Plugin 'yggdroot/indentline'                            "Muestra lineas verticales horizontales como están identadas
Plugin 'mattn/emmet-vim'                                "para tener emmet como en sublimetext
Plugin 'gko/vim-coloresque'                             "para mostrar los colores en #ffffff
Plugin 'joonty/vdebug'                                  "para realizar debug
Plugin 'raimondi/delimitmate'                           "para agregar llaves parentesis etc
Plugin 'ryanoasis/vim-devicons'                         "para agregar iconos
Plugin 'tiagofumo/vim-nerdtree-syntax-highlight'        "colorea los icons del nerd tree
Plugin 'editorconfig/editorconfig-vim'                  "editorconfig
Plugin 'leafgarland/typescript-vim'                     "validación de typescript
Plugin 'mhartington/vim-angular2-snippets'              "snippets para angular
Plugin 'vim-syntastic/syntastic'                        "in process
Plugin 'elzr/vim-json'                                  "Muestra/oculta las comillas en json


" ======================================
" ===== CONFIGURATIONS FOR PLUGINS =====
" ======================================

" ==> Plugin 'scrooloose/nerdtree'
map <C-u> :NERDTreeToggle<CR>


" ==> Plugin 'scrooloose/nerdcommenter'
filetype plugin on


" ==> Plugin 'sickill/vim-monokai' and 'NLKNguyen/papercolor-theme'
set t_Co=256                                            " This is may or may not needed.
set background=dark
colorscheme PaperColor


" ==> Plugin 'vim-airline/vim-airline-themes'
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#left_sep = ' '
let g:airline#extensions#tabline#left_alt_sep = '|'


" ==> Plugin 'kannokanno/previm'
let g:previm_open_cmd = 'google-chrome'
noremap <leader>m :PrevimOpen<cr>
augroup PrevimSettings
    autocmd!
    autocmd BufNewFile,BufRead *.{md,mdwn,mkd,mkdn,mark*} set filetype=markdown
augroup END


" ==> Plugin 'ntpeters/vim-better-whitespace'
autocmd BufEnter * EnableStripWhitespaceOnSave
let g:better_whitespace_filetypes_blacklist=[""]        "To disable this plugin for specific file types


" ==> Plugin 'majutsushi/tagbar'
nmap <F8> :TagbarToggle<CR>


" ==> Plugin 'matze/vim-move'
vmap <C-j> <Plug>MoveBlockDown
vmap <C-k> <Plug>MoveBlockUp


" ==> Plugin 'Valloric/YouCompleteMe'
let g:ycm_collect_identifiers_from_tags_files = 1             " Let YCM read tags from Ctags file
let g:ycm_use_ultisnips_completer = 1                         " Default 1, just ensure
let g:ycm_seed_identifiers_with_syntax = 1                    " Completion for programming language's keyword
let g:ycm_complete_in_comments = 1                            " Completion in comments
let g:ycm_complete_in_strings = 1                             " Completion in string


" ==> Plugin 'honza/vim-snippets'
let g:UltiSnipsExpandTrigger       = "<c-j>"
let g:UltiSnipsJumpForwardTrigger  = "<c-j>"
let g:UltiSnipsJumpBackwardTrigger = "<c-p>"
let g:UltiSnipsListSnippets        = "<c-k>"                  " List possible snippets based on current file


" ==> Plugin 'yggdroot/indentline'                            " Muestra lineas verticales horizontales como están identadas
let g:indentLine_char = '¦'


" ==> Plugin 'mattn/emmet-vim'                                " Emmet como en sublimetext
let g:user_emmet_mode='a'


" ==> Plugin 'ryanoasis/vim-devicons'                         " Agrega iconos
set encoding=utf-8
let g:airline_powerline_fonts = 1
set guifont=Sans\ Mono\ for\ Powerline\ Plus\ Nerd\ File\ Types\ 10


" ==> Plugin 'editorconfig/editorconfig-vim'                  " editorconfig
let g:EditorConfig_exclude_patterns = ['fugitive://.*']


" ==> Plugin 'leafgarland/typescript-vim'                     " validación de typescript
autocmd BufNewFile,BufRead *.ts setlocal filetype=typescript  " para detectar el .ts cuando se tiene instalado syntastic


" ==> Plugin 'vim-syntastic/syntastic'                        " in process
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*
let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0


" ==> Plugin 'elzr/vim-json'                                  " Muestra/oculta las comillas en json
set conceallevel=2


call vundle#end()                                             " required end of plugins


" ==================
" ===== GLOBAL =====
" ==================

" All of your Plugins must be added before the following line
filetype plugin indent on    " required


" ===== MAPLEADER =====
let mapleader=","


" ===== MODIFY INDENTING SETTINGS =====
set autoindent              " autoindent always ON.
set expandtab               " To insert space characters whenever the tab key is pressed
set shiftwidth=2           " spaces for autoindenting
set tabstop=2
set softtabstop=2           " remove a full pseudo-TAB when i press <BS>
autocmd FileType python setl tabstop=4|setl shiftwidth=4|setl softtabstop=4


" ===== RELATIVE NUMBERS LINE =====
set relativenumber
function! NumberToggle()
    if(&relativenumber == 1)
        set norelativenumber
    else
        set relativenumber
    endif
endfunc
noremap <leader>r :call NumberToggle()<cr>


" Some programming languages work better when only N spaces padding is used.
autocmd FileType html,css,sass,scss,javascript,styl setlocal sw=2 sts=2
autocmd FileType json setlocal sw=2 sts=2
autocmd FileType ruby,eruby setlocal sw=2 sts=2
autocmd FileType yaml setlocal sw=2 sts=2


execute "set colorcolumn=81"
hi ColorColumn guibg=#303030 ctermbg=236
set laststatus=2        " always show statusbar
set wildmenu            " enable visual wildmenu
set nowrap              " don't wrap long lines
set textwidth=120       " whithout limit
set wrapmargin=10       " whithout margin
set number              " show line numbers
set cursorline          " show cursor on line
set cursorcolumn        " show cursor on column


" ===== CUSTOM MAP =====
" Make window navigation less painful.
"map <C-h> <C-w>h
"map <C-j> <C-w>j
"map <C-k> <C-w>k
"map <C-l> <C-w>l
