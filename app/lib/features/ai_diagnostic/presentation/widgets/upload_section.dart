import 'dart:io';
import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';

class UploadSection extends StatelessWidget {
  final File? selectedImage;
  final VoidCallback onCamera;
  final VoidCallback onGallery;
  final VoidCallback? onAnalyze;
  final bool canAnalyze;

  const UploadSection({
    super.key,
    required this.selectedImage,
    required this.onCamera,
    required this.onGallery,
    this.onAnalyze,
    this.canAnalyze = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: onGallery,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            height: 220,
            decoration: BoxDecoration(
              color: AppColors.backgroundCard,
              borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
              border: Border.all(
                color: selectedImage != null
                    ? AppColors.neonGreen.withValues(alpha: 0.5)
                    : AppColors.borderDim,
                width: selectedImage != null ? 1.5 : 1,
              ),
            ),
            child: selectedImage != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
                    child: Image.file(
                      selectedImage!,
                      fit: BoxFit.cover,
                      width: double.infinity,
                    ),
                  )
                : const _EmptyPlaceholder(),
          ),
        ),
        const SizedBox(height: AppDimensions.spaceMD),
        Row(
          children: [
            Expanded(
              child: _PickerButton(
                icon: Icons.camera_alt_outlined,
                label: 'Camera',
                onTap: onCamera,
              ),
            ),
            const SizedBox(width: AppDimensions.spaceMD),
            Expanded(
              child: _PickerButton(
                icon: Icons.photo_library_outlined,
                label: 'Gallery',
                onTap: onGallery,
              ),
            ),
          ],
        ),
        if (canAnalyze) ...[
          const SizedBox(height: AppDimensions.spaceMD),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: onAnalyze,
              icon: const Icon(Icons.biotech_outlined),
              label: const Text('Analyze Plant'),
            ),
          ),
        ],
      ],
    );
  }
}

class _EmptyPlaceholder extends StatelessWidget {
  const _EmptyPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          padding: const EdgeInsets.all(AppDimensions.spaceMD),
          decoration: BoxDecoration(
            color: AppColors.neonGreenFaint,
            borderRadius: BorderRadius.circular(AppDimensions.radiusXL),
          ),
          child: const Icon(Icons.add_photo_alternate_outlined,
              color: AppColors.neonGreen, size: 36),
        ),
        const SizedBox(height: AppDimensions.spaceMD),
        const Text('Tap to select a plant image',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
        const SizedBox(height: 4),
        const Text('JPG, PNG up to 10 MB',
            style: TextStyle(color: AppColors.textMuted, fontSize: 14)),
      ],
    );
  }
}

class _PickerButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _PickerButton({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.textPrimary,
        side: const BorderSide(color: AppColors.borderDim),
        backgroundColor: AppColors.backgroundCard,
        padding: const EdgeInsets.symmetric(vertical: 14),
      ),
    );
  }
}
