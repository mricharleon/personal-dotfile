set number
set mouse=a
set numberwidth=1
set clipboard=unnamed
syntax enable
set showcmd
set ruler
set cursorline
set encoding=UTF-8
set showmatch
set sw=2
set relativenumber
set laststatus=2

call plug#begin('~/.vim/plugged')

" Themes
Plug 'morhetz/gruvbox'

" IDE
Plug 'easymotion/vim-easymotion'	" busca y mueve a coincidencias en el texto viible
Plug 'scrooloose/nerdtree'		" menu lateral
Plug 'christoomey/vim-tmux-navigator'	" navega con Ctrl entre ventanas de vim
Plug 'mattn/emmet-vim'			" emmet para vim
Plug 'Shougo/deoplete.nvim'		" autocompletar TS
Plug 'roxma/nvim-yarp'			" autocompletar TS
Plug 'roxma/vim-hug-neovim-rpc'		" autocompletar TS
Plug 'ryanoasis/vim-devicons'		" iconos en menu
Plug 'editorconfig/editorconfig-vim'
Plug 'https://github.com/AndrewRadev/tagalong.vim'
Plug 'https://tpope.io/vim/surround.git'		" completar parentesis, llaves etc
Plug 'https://tpope.io/vim/commentary.git'
Plug 'https://github.com/airblade/vim-gitgutter.git'
Plug 'Xuyuanp/nerdtree-git-plugin'
call plug#end()


" tema
colorscheme gruvbox
:set bg=dark

" NERDTree
let NERDTreeQuitOnOpen=1
let NERDTreeShowHidden=1

" Emmet
let g:user_emmet_install_global = 0
autocmd FileType html,css EmmetInstall
let g:user_emmet_leader_key='<C-Z>'

" Autocompletar TS
let g:deoplete#enable_at_startup = 1

" gitgutter
let g:gitgutter_terminal_reports_focus=0

" nerdtree-git-plugin
let g:NERDTreeIndicatorMapCustom = {
    \ "Modified"  : "✹",
    \ "Staged"    : "✚",
    \ "Untracked" : "✭",
    \ "Renamed"   : "➜",
    \ "Unmerged"  : "═",
    \ "Deleted"   : "✖",
    \ "Dirty"     : "✗",
    \ "Clean"     : "✔︎",
    \ "Ignored"   : "☒",
    \ "Unknown"   : "?"
    \ }

let mapleader=" "

" easymotion
nmap <Leader>s <Plug>(easymotion-s2)
" NERDTree
nmap <Leader>nt :NERDTreeFind<CR>
" Personales
nmap <Leader>w :w<CR>
nmap <Leader>q :q<CR>
