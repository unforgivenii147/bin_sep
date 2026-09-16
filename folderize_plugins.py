#!/data/data/com.termux/files/home/.local/bin/python
"""folderize_plugins.py – Folderize Plugins utilities.

This module provides functionality for folderize plugins."""
from __future__ import annotations
from typing import Any
import re
import shutil
from collections import defaultdict
from pathlib import Path
PLUGIN_PATTERNS = {'lazy.nvim': ['lazy\\.setup', 'lazy\\.nvim', 'require\\(["\\\']lazy["\\\']', '\\blazy\\b'], 'packer.nvim': ['packer\\.setup', 'packer\\.nvim', 'require\\(["\\\']packer["\\\']', '\\bpacker\\b'], 'vim-plug': ['vim-plug', 'plug#begin', '\\bPlug\\s+["\\\']'], 'telescope': ['telescope', 'require\\(["\\\']telescope["\\\']', 'telescope\\.setup'], 'fzf-lua': ['fzf-lua', 'fzf_lua', 'require\\(["\\\']fzf-lua["\\\']'], 'treesitter': ['treesitter', 'nvim-treesitter', 'tree-sitter', 'require\\(["\\\']nvim-treesitter["\\\']'], 'lualine': ['lualine', 'require\\(["\\\']lualine["\\\']', 'lualine\\.setup'], 'bufferline': ['bufferline', 'buffer-line', 'require\\(["\\\']bufferline["\\\']'], 'statuscol': ['statuscol', 'status-column', 'require\\(["\\\']statuscol["\\\']'], 'indent-blankline': ['indent-blankline', 'indent_blankline', 'ibl\\.setup', 'require\\(["\\\']ibl["\\\']'], 'mini.nvim': ['mini\\.', 'require\\(["\\\']mini\\.'], 'noice': ['noice', 'require\\(["\\\']noice["\\\']', 'noice\\.setup'], 'notify': ['nvim-notify', 'notify\\.setup', 'require\\(["\\\']notify["\\\']'], 'dressing': ['dressing', 'dressing\\.setup', 'require\\(["\\\']dressing["\\\']'], 'dashboard': ['dashboard-nvim', 'dashboard\\.setup', 'require\\(["\\\']dashboard["\\\']'], 'alpha': ['alpha-nvim', 'alpha\\.setup', 'require\\(["\\\']alpha["\\\']'], 'which-key': ['which-key', 'which_key', 'whichkey', 'require\\(["\\\']which-key["\\\']'], 'legendary': ['legendary', 'legendary\\.setup', 'require\\(["\\\']legendary["\\\']'], 'nvim-cmp': ['nvim-cmp', 'nvim_cmp', 'cmp\\.setup', 'require\\(["\\\']cmp["\\\']', 'require\\(["\\\']cmp_nvim'], 'lspconfig': ['lspconfig', 'nvim-lspconfig', 'require\\(["\\\']lspconfig["\\\']'], 'mason': ['mason', 'mason-nvim', 'mason-lspconfig', 'mason\\.setup', 'require\\(["\\\']mason["\\\']'], 'mason-lspconfig': ['mason-lspconfig', 'mason_lspconfig', 'require\\(["\\\']mason-lspconfig["\\\']'], 'mason-tool-installer': ['mason-tool-installer', 'mason_tool_installer', 'require\\(["\\\']mason-tool-installer["\\\']'], 'null-ls': ['null-ls', 'null_ls', 'require\\(["\\\']null-ls["\\\']'], 'none-ls': ['none-ls', 'none_ls', 'require\\(["\\\']none-ls["\\\']'], 'conform': ['conform', 'conform\\.setup', 'require\\(["\\\']conform["\\\']'], 'efm-langserver': ['efm-langserver', 'efm\\.setup', 'require\\(["\\\']efm["\\\']'], 'fidget': ['fidget', 'fidget\\.setup', 'require\\(["\\\']fidget["\\\']'], 'lsp-status': ['lsp-status', 'lsp_status', 'require\\(["\\\']lsp-status["\\\']'], 'lsp-signature': ['lsp-signature', 'lsp_signature', 'require\\(["\\\']lsp_signature["\\\']'], 'lsp-lines': ['lsp-lines', 'lsp_lines', 'require\\(["\\\']lsp_lines["\\\']'], 'goto-preview': ['goto-preview', 'goto_preview', 'require\\(["\\\']goto-preview["\\\']'], 'lspsaga': ['lspsaga', 'lspsaga\\.setup', 'require\\(["\\\']lspsaga["\\\']'], 'lsp-ui': ['lsp-ui', 'lsp_ui', 'require\\(["\\\']lspconfig["\\\'].*lsp-ui'], 'luasnip': ['luasnip', 'lua-snip', 'require\\(["\\\']luasnip["\\\']', 'ls\\.setup'], 'snippy': ['snippy', 'snippy\\.setup', 'require\\(["\\\']snippy["\\\']'], 'ultisnips': ['ultisnips', 'UltiSnips', 'ultisnips#'], 'friendly-snippets': ['friendly-snippets', 'friendly_snippets', 'require\\(["\\\']friendly-snippets["\\\']'], 'gitsigns': ['gitsigns', 'gitsigns\\.setup', 'require\\(["\\\']gitsigns["\\\']'], 'neogit': ['neogit', 'neogit\\.setup', 'require\\(["\\\']neogit["\\\']'], 'vim-fugitive': ['vim-fugitive', 'fugitive', ':Git\\b'], 'git-blame': ['git-blame', 'git_blame', 'gitblame'], 'gitlinker': ['gitlinker', 'git-linker', 'require\\(["\\\']gitlinker["\\\']'], 'diffview': ['diffview', 'diffview\\.setup', 'require\\(["\\\']diffview["\\\']'], 'octo': ['octo\\.nvim', 'octo\\.setup', 'require\\(["\\\']octo["\\\']'], 'git-conflict': ['git-conflict', 'git_conflict', 'git-conflict\\.setup'], 'neo-tree': ['neo-tree', 'neo_tree', 'neotree', 'require\\(["\\\']neo-tree["\\\']'], 'nvim-tree': ['nvim-tree', 'nvim_tree', 'require\\(["\\\']nvim-tree["\\\']', 'nvim-tree\\.setup'], 'oil': ['oil\\.setup', 'oil\\.nvim', 'require\\(["\\\']oil["\\\']', '\\boil\\b'], 'chad-tree': ['chad-tree', 'chad_tree', 'require\\(["\\\']nvchad'], 'harpoon': ['harpoon', 'harpoon2', 'require\\(["\\\']harpoon["\\\']', 'harpoon\\.setup'], 'hop': ['hop\\.setup', 'hop\\.nvim', 'require\\(["\\\']hop["\\\']'], 'leap': ['leap\\.setup', 'leap\\.nvim', 'require\\(["\\\']leap["\\\']'], 'flash': ['flash\\.setup', 'flash\\.nvim', 'require\\(["\\\']flash["\\\']'], 'easymotion': ['easymotion', 'easy-motion', 'vim-easymotion'], 'marks': ['marks\\.setup', 'marks\\.nvim', 'require\\(["\\\']marks["\\\']'], 'grapple': ['grapple', 'grapple\\.setup', 'require\\(["\\\']grapple["\\\']'], 'arrow': ['arrow\\.setup', 'arrow\\.nvim', 'require\\(["\\\']arrow["\\\']'], 'surround': ['nvim-surround', 'surround\\.setup', 'require\\(["\\\']nvim-surround["\\\']'], 'autopairs': ['nvim-autopairs', 'autopairs\\.setup', 'require\\(["\\\']nvim-autopairs["\\\']'], 'comment': ['comment\\.setup', 'nvim-comment', 'Comment\\.setup', 'require\\(["\\\']Comment["\\\']'], 'ts-comments': ['ts-comments', 'ts_comments', 'require\\(["\\\']ts-comments["\\\']'], 'tcomment': ['tcomment', 't-comment', 'vim-tcomment'], 'vim-commentary': ['vim-commentary', 'commentary'], 'dial': ['dial\\.setup', 'dial\\.nvim', 'require\\(["\\\']dial["\\\']'], 'substitute': ['substitute\\.setup', 'substitute\\.nvim', 'require\\(["\\\']substitute["\\\']'], 'ultimate-autopair': ['ultimate-autopair', 'ultimate_autopair'], 'vim-visual-multi': ['vim-visual-multi', 'visual-multi', 'visual_multi'], 'vim-illuminate': ['illuminate', 'vim-illuminate', 'illuminate\\.setup'], 'todo-comments': ['todo-comments', 'todo_comments', 'todocomments', 'require\\(["\\\']todo-comments["\\\']'], 'twilight': ['twilight\\.setup', 'twilight\\.nvim', 'require\\(["\\\']twilight["\\\']'], 'zen-mode': ['zen-mode', 'zen_mode', 'require\\(["\\\']zen-mode["\\\']', 'zen-mode\\.setup'], 'true-zen': ['true-zen', 'true_zen', 'require\\(["\\\']true-zen["\\\']'], 'colorizer': ['colorizer', 'nvim-colorizer', 'colorizer\\.setup'], 'highlight-colors': ['highlight-colors', 'highlight_colors', 'highlight-colors\\.setup'], 'vim-hexokinase': ['hexokinase', 'vim-hexokinase'], 'dap': ['nvim-dap', 'dap\\.setup', 'require\\(["\\\']dap["\\\']', '\\bdap\\b'], 'dap-ui': ['dap-ui', 'dapui', 'dap_ui', 'require\\(["\\\']dapui["\\\']'], 'dap-python': ['dap-python', 'dap_python', 'require\\(["\\\']dap-python["\\\']'], 'dap-go': ['dap-go', 'dap_go', 'require\\(["\\\']dap-go["\\\']'], 'nvim-dap-virtual-text': ['dap-virtual-text', 'dap_virtual_text', 'nvim-dap-virtual-text'], 'neotest': ['neotest', 'neotest\\.setup', 'require\\(["\\\']neotest["\\\']'], 'vim-test': ['vim-test', 'vim_test', 'vim-test#'], 'plenary': ['plenary', 'require\\(["\\\']plenary["\\\']'], 'toggleterm': ['toggleterm', 'toggle-term', 'toggleterm\\.setup', 'require\\(["\\\']toggleterm["\\\']'], 'floaterm': ['floaterm', 'float-term', 'floaterm#'], 'FTerm': ['FTerm\\.setup', 'ft-nvim', 'require\\(["\\\']FTerm["\\\']'], 'auto-session': ['auto-session', 'auto_session', 'auto-session\\.setup'], 'persistence': ['persistence\\.setup', 'persistence\\.nvim', 'require\\(["\\\']persistence["\\\']'], 'project': ['project\\.nvim', 'project\\.setup', 'require\\(["\\\']project_nvim["\\\']'], 'telescope-project': ['telescope-project', 'telescope_project', 'telescope._extensions.project'], 'trouble': ['trouble', 'trouble\\.setup', 'require\\(["\\\']trouble["\\\']'], 'spectre': ['spectre', 'spectre\\.setup', 'require\\(["\\\']spectre["\\\']'], 'nvim-bqf': ['bnf', 'nvim-bqf', 'bqf\\.setup'], 'vim-ripgrep': ['vim-ripgrep', 'Ripgrep', 'ripgrep#'], 'tagbar': ['tagbar', 'tag-bar', 'tagbar#'], 'vista': ['vista', 'vista\\.setup', 'vista#'], 'symbols-outline': ['symbols-outline', 'symbols_outline', 'symbols-outline\\.setup'], 'aerial': ['aerial\\.setup', 'aerial\\.nvim', 'require\\(["\\\']aerial["\\\']'], 'vim-dadbod': ['vim-dadbod', 'dadbod', 'dadbod#'], 'dadbod-ui': ['dadbod-ui', 'dadbod_ui', 'dadbod-ui\\.setup'], 'sqlite': ['sqlite\\.lua', 'sqlite', 'require\\(["\\\']sqlite["\\\']'], 'vim-go': ['vim-go', 'vim_go', '\\bgo#'], 'rust-tools': ['rust-tools', 'rust_tools', 'rust-tools\\.setup'], 'rustaceanvim': ['rustaceanvim', 'rustacean\\.setup', 'require\\(["\\\']rustaceanvim["\\\']'], 'vim-python': ['vim-python', 'python-mode', 'python-syntax'], 'vim-javascript': ['vim-javascript', 'javascript\\.vim', 'vim-js'], 'typescript-tools': ['typescript-tools', 'typescript\\.tools', 'typescript-tools\\.setup'], 'vim-vue': ['vim-vue', 'vim_vue', 'vue\\.vim'], 'vim-react': ['vim-react', 'vim_react', 'vim-jsx'], 'vim-markdown': ['vim-markdown', 'markdown\\.vim', 'vim_markdown'], 'markdown-preview': ['markdown-preview', 'markdown_preview', 'markdown-preview\\.setup'], 'vim-tex': ['vim-tex', 'vimtex', 'latex'], 'vim-julia': ['vim-julia', 'julia-vim', 'julia\\.vim'], 'vim-r': ['vim-r', 'vim_r', 'Nvim-R'], 'vim-scala': ['vim-scala', 'scala-vim', 'scala\\.vim'], 'undo-tree': ['undo-tree', 'undo_tree', 'undotree', 'undo-tree\\.setup'], 'whichkey': ['whichkey', 'which-key', 'which_key'], 'vim-repeat': ['vim-repeat', 'vim_repeat', 'repeat\\.vim'], 'vim-surround': ['vim-surround', 'vim_surround', 'surround\\.vim'], 'vim-unimpaired': ['vim-unimpaired', 'unimpaired', 'unimpaired\\.vim'], 'vim-abolish': ['vim-abolish', 'abolish', 'abolish\\.vim'], 'vim-speeddating': ['vim-speeddating', 'speeddating', 'speeddating\\.vim'], 'vim-exchange': ['vim-exchange', 'exchange', 'exchange\\.vim'], 'vim-characterize': ['vim-characterize', 'characterize', 'characterize\\.vim'], 'vim-textobj': ['vim-textobj', 'textobj', 'textobj-'], 'nvim-treesitter-textobjects': ['treesitter-textobjects', 'textobjects\\.setup', 'require\\(["\\\']nvim-treesitter-textobjects["\\\']'], 'splitjoin': ['splitjoin', 'split-join', 'splitjoin\\.vim'], 'vim-sort': ['vim-sort', 'sort\\.vim', '\\bsort#'], 'vim-easy-align': ['vim-easy-align', 'easy-align', 'easy_align', 'easy-align\\.setup'], 'tabular': ['tabular', 'tabular#', 'tabular\\.vim'], 'vim-argwrap': ['vim-argwrap', 'argwrap', 'argwrap\\.vim'], 'prettier': ['prettier', 'prettier\\.setup', 'vim-prettier', 'prettier-nvim'], 'eslint': ['eslint', 'eslint\\.setup', 'vim-eslint', 'eslint-nvim'], 'stylelint': ['stylelint', 'stylelint\\.setup', 'vim-stylelint'], 'ale': ['\\bale\\b', 'ale\\.vim', 'ale#', 'vim-ale'], 'vim-lint': ['vim-lint', 'vim_lint', 'lint\\.vim'], 'nvim-web-devicons': ['nvim-web-devicons', 'web-devicons', 'devicons\\.setup', 'require\\(["\\\']nvim-web-devicons["\\\']'], 'lspkind': ['lspkind', 'lsp-kind', 'lspkind\\.setup', 'require\\(["\\\']lspkind["\\\']'], 'vim-devicons': ['vim-devicons', 'vim_devicons', 'devicons'], 'nerd-fonts': ['nerd-fonts', 'nerd_fonts', 'nerdfonts'], 'tokyonight': ['tokyonight', 'tokyo-night', 'tokyonight\\.setup', 'tokyonight\\.load'], 'catppuccin': ['catppuccin', 'catppuccin\\.setup', 'catppuccin\\.load'], 'onedark': ['onedark', 'one-dark', 'onedark\\.setup', 'onedark\\.load'], 'gruvbox': ['gruvbox', 'gruvbox\\.setup', 'gruvbox\\.load'], 'nord': ['nord', 'nord\\.setup', 'nord\\.load'], 'rose-pine': ['rose-pine', 'rose_pine', 'rose-pine\\.setup', 'rose-pine\\.load'], 'kanagawa': ['kanagawa', 'kanagawa\\.setup', 'kanagawa\\.load'], 'github-theme': ['github-theme', 'github_theme', 'github-theme\\.setup'], 'dracula': ['dracula', 'dracula\\.setup', 'dracula\\.load'], 'everforest': ['everforest', 'ever-forest', 'everforest\\.setup'], 'material': ['material\\.setup', 'material\\.load', 'material-theme'], 'nightfox': ['nightfox', 'night-fox', 'nightfox\\.setup'], 'ayu': ['ayu', 'ayu-vim', 'ayu\\.setup'], 'solarized': ['solarized', 'solarized\\.setup', 'solarized\\.load'], 'melange': ['melange', 'melange\\.setup', 'melange\\.load'], 'vim-colorschemes': ['vim-colorschemes', 'colorschemes', 'vim_colorschemes'], 'impatient': ['impatient', 'impatient\\.setup', 'impatient\\.nvim'], 'vim-startuptime': ['vim-startuptime', 'startuptime', 'vim_startuptime'], 'profile': ['profile\\.nvim', 'profile\\.setup', 'require\\(["\\\']profile["\\\']'], 'vim-which-key': ['vim-which-key', 'vim_which_key', 'vim-whichkey'], 'keys': ['keys\\.setup', 'keys\\.nvim', 'require\\(["\\\']keys["\\\']'], 'cheatsheet': ['cheatsheet', 'cheat-sheet', 'cheat\\.setup'], 'vim-help': ['vim-help', 'help\\.vim', 'vim_help'], 'vim-tmux': ['vim-tmux', 'tmux\\.vim', 'vim_tmux', 'tmux-navigator'], 'tmux-navigator': ['tmux-navigator', 'tmux_navigator', 'tmux-navigator\\.setup'], 'vim-tmux-navigator': ['vim-tmux-navigator', 'vim_tmux_navigator'], 'window-picker': ['window-picker', 'window_picker', 'window-picker\\.setup'], 'winshift': ['winshift', 'win-shift', 'winshift\\.setup'], 'vim-maximizer': ['vim-maximizer', 'vim_maximizer', 'maximizer\\.vim'], 'zen-mode': ['zen-mode', 'zen_mode', 'zen-mode\\.setup'], 'focus': ['focus\\.nvim', 'focus\\.setup', 'require\\(["\\\']focus["\\\']'], 'scrollbar': ['scrollbar', 'scroll-bar', 'scrollbar\\.setup'], 'nvim-scrollview': ['nvim-scrollview', 'scrollview', 'scrollview\\.setup'], 'smoothscroll': ['smoothscroll', 'smooth-scroll', 'smooth-scroll\\.setup'], 'neoscroll': ['neoscroll', 'neo-scroll', 'neoscroll\\.setup'], 'vim-smoothie': ['vim-smoothie', 'smoothie', 'smoothie\\.vim'], 'vim-remote': ['vim-remote', 'remote\\.vim', 'vim_remote'], 'netrw': ['netrw', 'netrw\\.vim', 'netrw#'], 'vim-ssh': ['vim-ssh', 'ssh\\.vim', 'vim_ssh'], 'vim-scp': ['vim-scp', 'scp\\.vim', 'vim_scp'], 'vim-obsession': ['vim-obsession', 'obsession', 'obsession\\.vim'], 'vim-startify': ['vim-startify', 'startify', 'startify#'], 'vim-devicons': ['vim-devicons', 'vim_devicons', 'devicons\\.vim'], 'vim-projectionist': ['vim-projectionist', 'projectionist', 'projectionist#'], 'vim-dispatch': ['vim-dispatch', 'dispatch\\.vim', 'dispatch#'], 'vim-eunuch': ['vim-eunuch', 'eunuch', 'eunuch\\.vim'], 'vim-rails': ['vim-rails', 'rails\\.vim', 'vim_rails'], 'vim-ruby': ['vim-ruby', 'ruby\\.vim', 'vim_ruby'], 'vim-elixir': ['vim-elixir', 'elixir\\.vim', 'vim_elixir'], 'vim-clojure': ['vim-clojure', 'clojure\\.vim', 'vim_clojure'], 'vim-haskell': ['vim-haskell', 'haskell\\.vim', 'vim_haskell'], 'vim-lua': ['vim-lua', 'lua\\.vim', 'vim_lua'], 'vim-rust': ['vim-rust', 'rust\\.vim', 'vim_rust'], 'vim-crystal': ['vim-crystal', 'crystal\\.vim', 'vim_crystal'], 'vim-nim': ['vim-nim', 'nim\\.vim', 'vim_nim'], 'vim-zig': ['vim-zig', 'zig\\.vim', 'vim_zig'], 'vim-dart': ['vim-dart', 'dart\\.vim', 'vim_dart'], 'vim-flutter': ['vim-flutter', 'flutter\\.vim', 'vim_flutter'], 'vim-kotlin': ['vim-kotlin', 'kotlin\\.vim', 'vim_kotlin'], 'vim-swift': ['vim-swift', 'swift\\.vim', 'vim_swift'], 'vim-solidity': ['vim-solidity', 'solidity\\.vim', 'vim_solidity'], 'vim-php': ['vim-php', 'php\\.vim', 'vim_php'], 'vim-perl': ['vim-perl', 'perl\\.vim', 'vim_perl'], 'vim-ruby': ['vim-ruby', 'ruby\\.vim', 'vim_ruby'], 'vim-raku': ['vim-raku', 'raku\\.vim', 'vim_raku']}

def detect_plugins(path: Path | str) -> Any:
    """detect_plugins – detect plugins.

Args:
    path: Description of path."""
    detected = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        filename = path.name.lower()
        for plugin_name, patterns in PLUGIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.add(plugin_name)
                    break
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    detected.add(plugin_name)
                    break
    except Exception as e:
        print(f'Error reading {path}: {e}')
    return detected

def organize_files(dry_run: bool=False) -> None:
    """organize_files – organize files.

Args:
    dry_run: Description of dry_run."""
    current_dir = Path.cwd()
    lua_files = list(current_dir.rglob('*.lua'))
    if not lua_files:
        print('No .lua files found in the current directory tree.')
        return
    print(f'Found {len(lua_files)} .lua files')
    print('Scanning for plugin references...\n')
    plugin_files = defaultdict(list)
    unclassified_files = []
    for lua_file in lua_files:
        plugins = detect_plugins(lua_file)
        if plugins:
            for plugin in plugins:
                plugin_files[plugin].append(lua_file)
            print(f"  {lua_file.relative_to(current_dir)}: {', '.join(sorted(plugins))}")
        else:
            unclassified_files.append(lua_file)
            print(f'  {lua_file.relative_to(current_dir)}: No plugins detected')
    print('\n' + '=' * 40)
    print('Organization Plan:')
    print('=' * 40)
    for plugin in sorted(plugin_files.keys()):
        files = plugin_files[plugin]
        print(f'\n📁 {plugin}/ ({len(files)} files)')
        for file in files:
            print(f'  → {file.relative_to(current_dir)}')
    if unclassified_files:
        print(f'\n📁 unclassified/ ({len(unclassified_files)} files)')
        for file in unclassified_files:
            print(f'  → {file.relative_to(current_dir)}')
    if dry_run:
        print('\n[DRY RUN] No files were moved. Run without --dry-run to organize files.')
        return
    response = input('\nProceed with moving files? (y/N): ').strip().lower()
    if response not in ['y', 'yes']:
        print('Operation cancelled.')
        return
    print('\nMoving files...')
    moved_count = 0
    for plugin, files in plugin_files.items():
        plugin_folder = current_dir / plugin
        plugin_folder.mkdir(exist_ok=True)
        for file in files:
            try:
                destination = plugin_folder / file.name
                if destination.exists() and destination != file:
                    stem = file.stem
                    suffix = file.suffix
                    counter = 1
                    while destination.exists():
                        new_name = f'{stem}_{counter}{suffix}'
                        destination = plugin_folder / new_name
                        counter += 1
                    print(f'  ⚠️  Name conflict: {file.name} → {destination.name}')
                shutil.move(str(file), str(destination))
                moved_count += 1
                print(f'  ✓ {file.relative_to(current_dir)} → {destination.relative_to(current_dir)}')
            except Exception as e:
                print(f'  ✗ Failed to move {file}: {e}')
    if unclassified_files:
        unclassified_folder = current_dir / 'unclassified'
        unclassified_folder.mkdir(exist_ok=True)
        for file in unclassified_files:
            try:
                destination = unclassified_folder / file.name
                if destination.exists() and destination != file:
                    stem = file.stem
                    suffix = file.suffix
                    counter = 1
                    while destination.exists():
                        new_name = f'{stem}_{counter}{suffix}'
                        destination = unclassified_folder / new_name
                        counter += 1
                shutil.move(str(file), str(destination))
                moved_count += 1
                print(f'  ✓ {file.relative_to(current_dir)} → {destination.relative_to(current_dir)}')
            except Exception as e:
                print(f'  ✗ Failed to move {file}: {e}')
    print(f'\n✅ Completed! Moved {moved_count} files.')

def main() -> None:
    """main – main."""
    import argparse
    parser = argparse.ArgumentParser(description='Organize Neovim plugin files into folders by plugin name')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually moving files')
    args = parser.parse_args()
    organize_files(dry_run=args.dry_run)
if __name__ == '__main__':
    main()
