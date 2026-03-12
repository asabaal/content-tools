"""
Core module CLI entry point.

Usage:
    python -m core init --name "My Project" --path ./my-project
    python -m core init --name "Episode 4" --path ./projects/ep4 --season 0 --episode 4
    python -m core reset --path ./my-project
"""

import argparse
import shutil
import sys
from pathlib import Path

from .project_config import ProjectConfig, get_default_project_path


def cmd_init(args):
    """Initialize a new project."""
    data_dir = Path(args.path)
    
    try:
        config = ProjectConfig.create(
            data_dir=data_dir,
            name=args.name,
            season=args.season,
            episode=args.episode,
            description=args.description or ""
        )
        
        print(f"Created project: {config.name}")
        print(f"Project file: {config.path}")
        print(f"Data directory: {config.data_dir}")
        print("\nDirectory structure:")
        print(f"  {config.data_dir}/raw/         (add video files here)")
        print(f"  {config.data_dir}/transcripts/ (transcripts will be generated here)")
        print(f"  {config.data_dir}/output/     (rendered output will go here)")
        
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_migrate(args):
    """Migrate a v1 project.json to v2 schema."""
    project_path = Path(args.project)
    
    if project_path.is_file() and project_path.name == 'project.json':
        config_path = project_path
    elif (project_path / 'project.json').exists():
        config_path = project_path / 'project.json'
    else:
        print(f"Error: Project not found: {project_path}", file=sys.stderr)
        sys.exit(1)
    
    config = ProjectConfig.load(config_path)
    
    print(f"Migrated project: {config.name}")
    print(f"Project file: {config.path}")


def cmd_reset(args):
    """Reset project state, preserving only raw video files."""
    project_path = Path(args.project)
    
    if project_path.is_file() and project_path.name == 'project.json':
        config_path = project_path
        data_dir = project_path.parent
    elif (project_path / 'project.json').exists():
        config_path = project_path / 'project.json'
        data_dir = project_path
    else:
        print(f"Error: Project not found: {project_path}", file=sys.stderr)
        sys.exit(1)
    
    config = ProjectConfig.load(config_path)
    
    items_to_delete = []
    items_preserved = []
    
    if config.transcripts_dir.exists():
        items_to_delete.append(('directory', config.transcripts_dir))
    
    if config.combined_transcript.exists():
        items_to_delete.append(('file', config.combined_transcript))
    
    if config.combined_video.exists():
        items_to_delete.append(('file', config.combined_video))
    
    if config.waveforms.exists():
        items_to_delete.append(('file', config.waveforms))
    
    if config.output_dir.exists():
        items_to_delete.append(('directory', config.output_dir))
    
    if config.raw_dir.exists():
        items_preserved.append(('directory', config.raw_dir))
    
    print(f"Project: {config.name}")
    print(f"Location: {data_dir}")
    print()
    
    if not items_to_delete:
        print("Nothing to reset - project is already clean.")
        return
    
    print("WILL BE DELETED:")
    for item_type, item_path in items_to_delete:
        print(f"  [{item_type}] {item_path.name}")
    print()
    
    print("WILL BE PRESERVED:")
    if items_preserved:
        for item_type, item_path in items_preserved:
            file_count = len(list(item_path.iterdir())) if item_path.is_dir() else 0
            print(f"  [{item_type}] {item_path.name}/ ({file_count} files)")
    else:
        print("  (nothing)")
    print()
    
    response = input(f"Reset project '{config.name}'? This cannot be undone. [y/N] ")
    
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    print()
    for item_type, item_path in items_to_delete:
        try:
            if item_type == 'directory':
                shutil.rmtree(item_path)
                print(f"  Deleted directory: {item_path.name}/")
            else:
                item_path.unlink()
                print(f"  Deleted file: {item_path.name}")
        except Exception as e:
            print(f"  ERROR deleting {item_path.name}: {e}", file=sys.stderr)
    
    # Reset project.json - preserve metadata and raw path, clear everything else
    config._raw_data = {"clips": [], "videos": []}
    config.paths = {"raw": "raw"}
    config.save()
    print(f"  Reset: {config.path.name}")
    
    print()
    print(f"Project '{config.name}' has been reset.")
    print("Run Tool 1 (transcribe) to regenerate project files.")


def main():
    parser = argparse.ArgumentParser(
        description="Core module commands",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    init_parser = subparsers.add_parser('init', help='Initialize a new project')
    init_parser.add_argument('--name', '-n', required=True, help='Project name')
    init_parser.add_argument('--path', '-p', default='./my-project', help='Project directory path')
    init_parser.add_argument('--season', type=int, help='Season number')
    init_parser.add_argument('--episode', type=int, help='Episode number')
    init_parser.add_argument('--description', '-d', default='', help='Project description')
    init_parser.set_defaults(func=cmd_init)
    
    migrate_parser = subparsers.add_parser('migrate', help='Migrate v1 project to v2 schema')
    migrate_parser.add_argument('--project', '-p', default='data', help='Path to project directory')
    migrate_parser.set_defaults(func=cmd_migrate)
    
    reset_parser = subparsers.add_parser('reset', help='Reset project state (preserves raw videos)')
    reset_parser.add_argument('--project', '-p', default='data', help='Path to project directory')
    reset_parser.set_defaults(func=cmd_reset)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
