import 'package:flutter/material.dart';
import '../../domain/entities/diagnosis_entity.dart';

class ResultCard extends StatelessWidget {
  final DiagnosisEntity diagnosis;
  const ResultCard({super.key, required this.diagnosis});
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .80);
    final color = diagnosis.isInconclusive ? muted : diagnosis.isHealthy ? cs.primary : const Color(0xFFE1B66B);
    return Container(
      width: double.infinity, padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(22), border: Border.all(color: color.withValues(alpha: .3))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(diagnosis.isInconclusive ? 'TRY A CLEARER PHOTO' : 'MODEL SUGGESTION',
          style: TextStyle(color: color, fontSize: 12, letterSpacing: 1.8, fontWeight: FontWeight.w700)),
        const SizedBox(height: 12),
        Text(diagnosis.diseaseName, style: TextStyle(color: cs.onSurface, fontSize: 30, fontWeight: FontWeight.w600, letterSpacing: -.9)),
        const SizedBox(height: 18),
        Text(diagnosis.description, style: TextStyle(color: muted, height: 1.7, fontSize: 14)),
        const SizedBox(height: 24),
        Row(children: [Text('Model confidence', style: TextStyle(color: muted)), const Spacer(),
          Text('${diagnosis.confidencePercent}%', style: TextStyle(color: color, fontWeight: FontWeight.w700))]),
        const SizedBox(height: 9),
        ClipRRect(borderRadius: BorderRadius.circular(6), child: LinearProgressIndicator(
          value: diagnosis.confidenceScore, minHeight: 5, color: color, backgroundColor: color.withValues(alpha: .12))),
        const SizedBox(height: 20),
        Text(diagnosis.treatment, style: TextStyle(color: muted, fontSize: 14, height: 1.6)),
        const SizedBox(height: 18),
        Wrap(spacing: 18, runSpacing: 6, children: [
          Text('Processed on this phone', style: TextStyle(color: cs.primary, fontSize: 13)),
          if (diagnosis.processingMilliseconds != null)
            Text('${diagnosis.processingMilliseconds} ms inference', style: TextStyle(color: muted, fontSize: 13)),
        ]),
      ]),
    );
  }
}
