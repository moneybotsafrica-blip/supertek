import os
from PIL import Image
import io
import tempfile

def compress_images(directory, quality=80, max_width=1920):
    """
    Compress images in the given directory and subdirectories, only if it reduces size.
    
    Args:
        directory: Root directory to search for images
        quality: JPEG quality (1-100, default 80)
        max_width: Maximum width for images (default 1920)
    """
    supported_formats = ('.jpg', '.jpeg', '.png', '.webp')
    compressed_count = 0
    skipped_count = 0
    total_original_size = 0
    total_compressed_size = 0
    space_saved = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_formats):
                file_path = os.path.join(root, file)
                
                try:
                    # Get original file size
                    original_size = os.path.getsize(file_path)
                    total_original_size += original_size
                    
                    # Skip if file is too small (< 50KB) - likely already optimized
                    if original_size < 51200:  # 50KB
                        skipped_count += 1
                        total_compressed_size += original_size
                        continue
                    
                    # Open image
                    with Image.open(file_path) as img:
                        # Convert RGBA to RGB for JPEG
                        original_mode = img.mode
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Resize if too large
                        width, height = img.size
                        needs_resize = width > max_width
                        if needs_resize:
                            ratio = max_width / width
                            new_height = int(height * ratio)
                            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Try compression to memory first to check if it helps
                        with io.BytesIO() as output:
                            if file.lower().endswith('.png'):
                                # For PNG, use optimize
                                img.save(output, 'PNG', optimize=True)
                            elif file.lower().endswith('.webp'):
                                # For WebP, use quality parameter
                                img.save(output, 'WEBP', quality=quality, method=6)
                            else:
                                # For JPEG, use quality parameter
                                img.save(output, 'JPEG', quality=quality, optimize=True, progressive=True)
                            
                            compressed_size = output.tell()
                        
                        # Only save if compression actually reduces size
                        if compressed_size < original_size:
                            # Save the compressed version
                            with Image.open(file_path) as img:
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    img = img.convert('RGB')
                                
                                if needs_resize:
                                    width, height = img.size
                                    if width > max_width:
                                        ratio = max_width / width
                                        new_height = int(height * ratio)
                                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                                
                                if file.lower().endswith('.png'):
                                    img.save(file_path, 'PNG', optimize=True)
                                elif file.lower().endswith('.webp'):
                                    img.save(file_path, 'WEBP', quality=quality, method=6)
                                else:
                                    img.save(file_path, 'JPEG', quality=quality, optimize=True, progressive=True)
                            
                            total_compressed_size += compressed_size
                            space_saved += (original_size - compressed_size)
                            
                            compression_ratio = (1 - (compressed_size / original_size)) * 100
                            compressed_count += 1
                            print(f"Compressed: {file_path}")
                            print(f"  Original: {original_size:,} bytes")
                            print(f"  Compressed: {compressed_size:,} bytes")
                            print(f"  Reduction: {compression_ratio:.1f}%")
                            print()
                        else:
                            # Skip compression - it would increase size
                            skipped_count += 1
                            total_compressed_size += original_size
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    skipped_count += 1
                    total_compressed_size += original_size
    
    # Print summary
    print("\n" + "="*50)
    print("COMPRESSION SUMMARY")
    print("="*50)
    print(f"Total images processed: {compressed_count}")
    print(f"Images skipped (no benefit): {skipped_count}")
    print(f"Total original size: {total_original_size:,} bytes ({total_original_size / (1024*1024):.2f} MB)")
    print(f"Total compressed size: {total_compressed_size:,} bytes ({total_compressed_size / (1024*1024):.2f} MB)")
    if total_original_size > 0:
        total_reduction = (1 - (total_compressed_size / total_original_size)) * 100
        print(f"Total reduction: {total_reduction:.1f}%")
        print(f"Space saved: {space_saved:,} bytes ({space_saved / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    # Use the neutrikenya directory
    project_dir = r"C:\Users\Moneybots\Downloads\neutrikenya\neutrikenya"
    
    print("Starting image compression...")
    print(f"Target directory: {project_dir}")
    print(f"Quality: 85")
    print(f"Max width: 1920px")
    print("-" * 50)
    
    compress_images(project_dir, quality=85, max_width=1920)
    
    print("\nCompression completed!")