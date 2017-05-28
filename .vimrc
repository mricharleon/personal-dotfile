set nocompatible                                        " be iMproved, required
filetype off                                            " required


" ===== RUNTIME PATH TO INCLUDE VUNDLE AND INITIALIZE =====
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()


" ===== PLUGINS VUDLE =====
Plugin 'VundleVim/Vundle.vim'

Plugin 'tpope/vim-fugitive'								"git tools
Plugin 'git://git.wincent.com/command-t.git'			"Don't know yet
Plugin 'rstacruz/sparkup', {'rtp': 'vim/'}				"Don't know yet
Plugin 'scrooloose/nerdtree'							"Files tree
Plugin 'Xuyuanp/nerdtree-git-plugin'                    "show git icons on tree
Plugin 'git://github.com/airblade/vim-gitgutter.git'    "show git icons on code
Plugin 'kien/ctrlp.vim'                                 "buscador global
Plugin 'scrooloose/nerdcommenter'                       "for comment code (don't work yet!)
Plugin 'majutsushi/tagbar'                              "show functions, import, etc.
Plugin 'sickill/vim-monokai'                            "color scheme by monokai
Plugin 'terryma/vim-multiple-cursors'                   "multiple curosors
Plugin 'vim-airline/vim-airline'                        "state bar
Plugin 'vim-airline/vim-airline-themes'                 "state bar
Plugin 'Valloric/YouCompleteMe'                         "complete some codes
Plugin 'kannokanno/previm'                              "show .md in real time
Plugin 'ntpeters/vim-better-whitespace'                 "remove whitespaces


" ===== CONFIGURATIONS FOR PLUGINS =====

" Plugin 'scrooloose/nerdtree'
" open/close menu
map <C-u> :NERDTreeToggle<CR>

" Plugin 'scrooloose/nerdcommenter'
filetype plugin on

" Plugin 'sickill/vim-monokai'
syntax enable
colorscheme monokai

" Plugin 'vim-airline/vim-airline-themes'
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#left_sep = ' '
let g:airline#extensions#tabline#left_alt_sep = '|'


" Plugin 'kannokanno/previm'
let g:previm_open_cmd = 'google-chrome'
nmap <F5> :PrevimOpen<CR>
augroup PrevimSettings
    autocmd!
    autocmd BufNewFile,BufRead *.{md,mdwn,mkd,mkdn,mark*} set filetype=markdown
augroup END

" Plugin 'ntpeters/vim-better-whitespace'
autocmd BufEnter * EnableStripWhitespaceOnSave
let g:better_whitespace_filetypes_blacklist=[""]        "To disable this plugin for specific file types

" Plugin 'majutsushi/tagbar'
nmap <F8> :TagbarToggle<CR>


" ===== DEFAULT =====
" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required

let mapleader=","


" ===== MODIFY INDENTING SETTINGS =====
set autoindent              " autoindent always ON.
set expandtab               " To insert space characters whenever the tab key is pressed
set shiftwidth=4            " spaces for autoindenting
set tabstop=4
set softtabstop=4           " remove a full pseudo-TAB when i press <BS>

" Some programming languages work better when only 2 spaces padding is used.
autocmd FileType html,css,sass,scss,javascript,styl setlocal sw=2 sts=2
autocmd FileType json setlocal sw=2 sts=2
autocmd FileType ruby,eruby setlocal sw=2 sts=2
autocmd FileType yaml setlocal sw=2 sts=2

set colorcolumn=80      " define columns limit
set laststatus=2        " always show statusbar
set wildmenu            " enable visual wildmenu
set nowrap              " don't wrap long lines
set textwidth=0         " whithout limit
set wrapmargin=10       " whithout margin
set number              " show line numbers
set cursorline          " show cursor on line
set cursorcolumn        " show cursor on column


" ===== CUSTOM MAP =====
" Make window navigation less painful.
map <C-h> <C-w>h
map <C-j> <C-w>j
map <C-k> <C-w>k
map <C-l> <C-w>l
