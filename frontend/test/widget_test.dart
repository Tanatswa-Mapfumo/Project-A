import 'package:flutter_test/flutter_test.dart';

import 'package:app_designs/main.dart';

void main() {
  testWidgets('Welcome screen shows the primary CTA', (WidgetTester tester) async {
    await tester.pumpWidget(const AppDesignsApp());
    await tester.pump();

    expect(find.text('Get Started'), findsOneWidget);
    expect(find.textContaining('Log In'), findsWidgets);
  });
}
