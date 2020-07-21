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
set splitright

set hidden
set cmdheight=2

call plug#begin('~/.vim/plugged')

" Themes
Plug 'morhetz/gruvbox'

" IDE
Plug 'easymotion/vim-easymotion'	" busca y mueve a coincidencias en el texto viible
Plug 'scrooloose/nerdtree'		" menu lateral
Plug 'christoomey/vim-tmux-navigator'	" navega con Ctrl entre ventanas de vim
Plug 'mattn/emmet-vim'			" emmet para vim
" Plug 'Shougo/deoplete.nvim'		" autocompletar TS
" Plug 'roxma/nvim-yarp'			" autocompletar TS
" Plug 'roxma/vim-hug-neovim-rpc'		" autocompletar TS
Plug 'ryanoasis/vim-devicons'		" iconos en menu
Plug 'editorconfig/editorconfig-vim'
Plug 'https://github.com/AndrewRadev/tagalong.vim'
Plug 'https://tpope.io/vim/surround.git'    " completar parentesis, llaves etc
Plug 'https://tpope.io/vim/commentary.git'
Plug 'https://github.com/airblade/vim-gitgutter.git'
Plug 'Xuyuanp/nerdtree-git-plugin'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'valloric/youcompleteme'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
call plug#end()


" tema
colorscheme gruvbox
:set bg=dark

" NERDTree
let NERDTreeQuitOnOpen=1
let NERDTreeShowHidden=1
let g:webdevicons_enable = 1
let g:webdevicons_enable_nerdtree = 1
let g:webdevicons_enable_vimfiler = 1
let g:webdevicons_enable_airline_tabline = 1
let g:webdevicons_enable_ctrlp = 1
let g:WebDevIconsUnicodeDecorateFileNodesDefaultSymbol = 'ƛ'

" Emmet
let g:user_emmet_install_global = 0
autocmd FileType html,css EmmetInstall
let g:user_emmet_leader_key='<C-Z>'

" Autocompletar TS
" let g:deoplete#enable_at_startup = 1

" gitgutter
let g:gitgutter_terminal_reports_focus=0

" " nerdtree-git-plugin
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

" tagalong
let g:tagalong_verbose = 1

let mapleader=" "

" easymotion
nmap <Leader>s <Plug>(easymotion-s2)
" NERDTree
nmap <Leader>nt :NERDTreeFind<CR>
" Personales
nmap <Leader>w :w<CR>
nmap <Leader>q :q<CR>
nmap <Leader>t :vert :term<CR>
vmap <Leader>c "+y
vmap <Leader>p "+p

" Use `[g` and `]g` to navigate diagnostics
" " Use `:CocDiagnostics` to get all diagnostics of current buffer in location
" list.
nmap <silent> [g <Plug>(coc-diagnostic-prev)
nmap <silent> ]g <Plug>(coc-diagnostic-next)

" " GoTo code navigation.
nmap <silent> gd <Plug>(coc-definition)
nmap <silent> gy <Plug>(coc-type-definition)
nmap <silent> gi <Plug>(coc-implementation)
nmap <silent> gr <Plug>(coc-references)

" Use K to show documentation in preview window.
nnoremap <silent> K :call <SID>show_documentation()<CR>

function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  else
    call CocAction('doHover')
  endif
endfunction

" Highlight the symbol and its references when holding the cursor.
autocmd CursorHold * silent call CocActionAsync('highlight')
" Symbol renaming.
nmap <leader>rn <Plug>(coc-rename)
" Formatting selected code.
xmap <leader>f  <Plug>(coc-format-selected)
nmap <leader>f  <Plug>(coc-format-selected)

" Having longer updatetime (default is 4000 ms = 4 s) leads to noticeable
" delays and poor user experience.
set updatetime=300
" Don't pass messages to |ins-completion-menu|.
set shortmess+=c
" Always show the signcolumn, otherwise it would shift the text each time
" diagnostics appear/become resolved.
if has("patch-8.1.1564")
  " Recently vim can merge signcolumn and number column into one
  set signcolumn=number
else
  set signcolumn=yes
endif

" Use tab for trigger completion with characters ahead and navigate.
" NOTE: Use command ':verbose imap <tab>' to make sure tab is not mapped by
" other plugin before putting this into your config.
inoremap <silent><expr> <TAB>
  \ pumvisible() ? "\<C-n>" :
  \ <SID>check_back_space() ? "\<TAB>" :
  \ coc#refresh()
inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : \<C-h>"

function! s:check_back_space() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

" Use <c-space> to trigger completion.
if has('nvim')
  inoremap <silent><expr> <c-space> coc#refresh()
else
  inoremap <silent><expr> <c-@> coc#refresh()
endif

" Use <cr> to confirm completion, `<C-g>u` means break undo chain at current
" position. Coc only does snippet and additional edit on confirm.
" <cr> could be remapped by other vim plugin, try `:verbose imap <CR>`.
if exists('*complete_info')
  inoremap <expr> <cr> complete_info()["selected"] != "-1" ? "\<C-y>" : "\<C-g>u\<CR>"
else
  inoremap <expr> <cr> pumvisible() ? "\<C-y>" : "\<C-g>u\<CR>"
endif
