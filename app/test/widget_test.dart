import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:agri_drone_ai/features/ai_diagnostic/data/datasources/plant_disease_classifier.dart';
import 'package:agri_drone_ai/features/ai_diagnostic/presentation/widgets/result_card.dart';

void main() {
  test('uncertain or unsupported classes never become healthy', () {
    for (final result in [
      PlantDiseaseKnowledge.diagnosisFor('Tomato___healthy', .89),
      PlantDiseaseKnowledge.diagnosisFor('unrecognized', .99),
      PlantDiseaseKnowledge.diagnosisFor('Tomato___healthy', double.nan),
    ]) {
      expect(result.isInconclusive, isTrue);
      expect(result.isHealthy, isFalse);
      expect(result.diseaseName, 'Inconclusive');
    }
    expect(PlantDiseaseKnowledge.diagnosisFor('Tomato___healthy', .90).isHealthy, isTrue);
    final disease = PlantDiseaseKnowledge.diagnosisFor('Tomato___Late_blight', .95);
    expect(disease.diseaseName, 'Late blight');
    expect(disease.affectedAreas, isEmpty);
  });

  testWidgets('inconclusive result shows measured confidence, no fabricated severity', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(
      child: ResultCard(diagnosis: PlantDiseaseKnowledge.diagnosisFor('Tomato___healthy', .58,
        processingMilliseconds: 27)),
    ))));
    expect(find.text('Inconclusive'), findsOneWidget);
    expect(find.text('58%'), findsOneWidget);
    expect(find.text('27 ms inference'), findsOneWidget);
    expect(find.text('Processed on this phone'), findsOneWidget);
    expect(find.textContaining('Severity'), findsNothing);
    expect(find.textContaining('Affected areas'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
