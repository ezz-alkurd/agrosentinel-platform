import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_dimensions.dart';

/// A beautiful horizontal carousel of theme swatches.
/// Tapping a swatch calls [onThemeSelected] with the palette id.
class ThemePicker extends StatelessWidget {
  final String selectedId;
  final ValueChanged<String> onThemeSelected;

  const ThemePicker({
    super.key,
    required this.selectedId,
    required this.onThemeSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 110,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: AppDimensions.spaceMD),
        itemCount: AppThemePalette.all.length,
        separatorBuilder: (_, __) => const SizedBox(width: AppDimensions.spaceMD),
        itemBuilder: (context, index) {
          final palette = AppThemePalette.all[index];
          return _ThemeSwatch(
            palette: palette,
            isSelected: palette.id == selectedId,
            onTap: () => onThemeSelected(palette.id),
          );
        },
      ),
    );
  }
}

class _ThemeSwatch extends StatefulWidget {
  final AppThemePalette palette;
  final bool isSelected;
  final VoidCallback onTap;

  const _ThemeSwatch({
    required this.palette,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_ThemeSwatch> createState() => _ThemeSwatchState();
}

class _ThemeSwatchState extends State<_ThemeSwatch>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 120),
    );
    _scale = Tween(begin: 1.0, end: 0.92).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.palette;

    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: 80,
          decoration: BoxDecoration(
            color: p.scaffold,
            borderRadius: BorderRadius.circular(AppDimensions.radiusLG),
            border: Border.all(
              color: widget.isSelected ? p.primary : p.primary.withValues(alpha: 0.2),
              width: widget.isSelected ? 2.0 : 1.0,
            ),
            boxShadow: widget.isSelected
                ? [
                    BoxShadow(
                      color: p.primary.withValues(alpha: 0.4),
                      blurRadius: 12,
                      spreadRadius: 0,
                    )
                  ]
                : [],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Gradient circle preview
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: p.gradientColors,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: p.primary.withValues(alpha: 0.5),
                      blurRadius: 8,
                    )
                  ],
                ),
                child: widget.isSelected
                    ? Icon(Icons.check_rounded,
                        color: p.brightness == Brightness.dark
                            ? Colors.black
                            : Colors.white,
                        size: 18)
                    : Center(
                        child: Text(p.emoji,
                            style: const TextStyle(fontSize: 16))),
              ),
              const SizedBox(height: 8),
              Text(
                p.label,
                style: TextStyle(
                  color: widget.isSelected ? p.primary : p.textSub,
                  fontSize: 11,
                  fontWeight: widget.isSelected
                      ? FontWeight.w700
                      : FontWeight.w500,
                ),
                textAlign: TextAlign.center,
                maxLines: 2,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
