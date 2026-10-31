import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import '../cubit/diagnostic_cubit.dart';
import '../cubit/diagnostic_state.dart';
import '../widgets/result_card.dart';

class AiDiagnosticPage extends StatefulWidget {
  final bool standalone;
  const AiDiagnosticPage({super.key, this.standalone = false});
  @override
  State<AiDiagnosticPage> createState() => _AiDiagnosticPageState();
}

class _AiDiagnosticPageState extends State<AiDiagnosticPage> {
  @override
  void initState() {
    super.initState();
    context.read<DiagnosticCubit>().recoverLostImage();
  }
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .80);
    return Scaffold(
      appBar: AppBar(title: const Text('Leaf analysis'),
        leading: widget.standalone ? IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.go('/login')) : null),
      body: BlocBuilder<DiagnosticCubit, DiagnosticState>(builder: (context, state) {
        final busy = state is DiagnosticAnalyzing;
        File? image;
        if (state is DiagnosticImageSelected) image = state.image;
        if (state is DiagnosticAnalyzing) image = state.image;
        if (state is DiagnosticResult) image = state.image;
        if (state is DiagnosticError) image = state.image;
        return SingleChildScrollView(padding: const EdgeInsets.fromLTRB(22, 12, 22, 32), child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [Container(width: 6, height: 6, decoration: BoxDecoration(color: cs.primary, shape: BoxShape.circle)),
              const SizedBox(width: 8), Text('ON-DEVICE ANALYSIS', style: TextStyle(color: cs.primary, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 1.7))]),
            const SizedBox(height: 15),
            Text('Tomato leaf analysis', style: TextStyle(color: cs.onSurface, fontSize: 30, height: 1.12, fontWeight: FontWeight.w600, letterSpacing: -1.3)),
            const SizedBox(height: 15),
            Text('Photograph a single tomato leaf. Analysis runs on your phone, even without internet.', style: TextStyle(color: muted, fontSize: 14, height: 1.7)),
            const SizedBox(height: 13),
            Text('Early blight  /  Late blight  /  Healthy', style: TextStyle(color: cs.primary, fontSize: 14)),
            const SizedBox(height: 26),
            if (image == null) Container(
              width: double.infinity, padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 38),
              decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(22), border: Border.all(color: cs.primary.withValues(alpha: .16))),
              child: Column(children: [Icon(Icons.photo_camera_outlined, size: 44, color: cs.primary), const SizedBox(height: 18),
                Text('Start with a clear photo', style: TextStyle(color: cs.onSurface, fontSize: 19, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10), Text('Fill the frame with one leaf. Use natural light and keep the camera steady.', textAlign: TextAlign.center, style: TextStyle(color: muted, height: 1.6))]))
            else ClipRRect(borderRadius: BorderRadius.circular(22), child: AspectRatio(aspectRatio: 4 / 3, child: Image.file(image, fit: BoxFit.cover, cacheWidth: 1024, errorBuilder: (_, error, stack) => const Center(child: Text('Cannot preview this photo'))))),
            const SizedBox(height: 18),
            if (!busy) Row(children: [
              Expanded(child: OutlinedButton.icon(icon: const Icon(Icons.camera_alt_outlined, size: 19), label: const Text('Camera'), onPressed: () => context.read<DiagnosticCubit>().pickImage(ImageSource.camera))),
              const SizedBox(width: 12),
              Expanded(child: OutlinedButton.icon(icon: const Icon(Icons.photo_library_outlined, size: 19), label: const Text('Gallery'), onPressed: () => context.read<DiagnosticCubit>().pickImage(ImageSource.gallery))),
            ]),
            if (state is DiagnosticImageSelected || state is DiagnosticError && image != null) ...[
              const SizedBox(height: 14),
              FilledButton.icon(onPressed: () => context.read<DiagnosticCubit>().analyzeCurrentImage(), icon: const Icon(Icons.center_focus_strong_outlined), label: Text(state is DiagnosticError ? 'Try analysis again' : 'Analyze leaf')),
            ],
            if (busy) Container(width: double.infinity, padding: const EdgeInsets.all(24),
              child: Row(children: [SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: cs.primary)), const SizedBox(width: 16),
                Expanded(child: Text('Analyzing on your phone…\nThe first analysis also loads the model.', style: TextStyle(color: muted, height: 1.7)))])),
            if (state is DiagnosticResult) ...[const SizedBox(height: 22), ResultCard(diagnosis: state.diagnosis)],
            if (state is DiagnosticError) ...[const SizedBox(height: 18), Container(width: double.infinity, padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: cs.error.withValues(alpha: .08), borderRadius: BorderRadius.circular(16)),
              child: Text(state.message.replaceFirst('Exception: ', '').replaceFirst('Bad state: ', ''), style: TextStyle(color: cs.error, height: 1.6)))],
            const SizedBox(height: 22),
            Text('Close-up tomato leaves only. A high score does not confirm plant health or cover other crops.', style: TextStyle(color: muted, fontSize: 13, height: 1.7)),
          ]));
      }),
    );
  }
}
