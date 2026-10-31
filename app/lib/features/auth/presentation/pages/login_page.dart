import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../bloc/auth_bloc.dart';
import '../bloc/auth_event.dart';
import '../bloc/auth_state.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});
  @override
  State<LoginPage> createState() => _LoginPageState();
}
class _LoginPageState extends State<LoginPage> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _obscure = true;
  @override
  void dispose() { _email.dispose(); _password.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final muted = cs.onSurface.withValues(alpha: .65);
    return Scaffold(body: BlocListener<AuthBloc, AuthState>(listener: (context, state) {
      if (state is AuthAuthenticated) context.go('/home');
      if (state is AuthError) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message)));
      if (state is AuthPasswordResetSent) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password reset email sent.')));
    }, child: SafeArea(child: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(26), child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 460), child: Form(key: _form, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SizedBox(height: 20),
      Row(children: [Image.asset('assets/branding/agrosentinel-mark.png', width: 48, height: 48), const SizedBox(width: 12), Text('AgroSentinel', style: TextStyle(color: cs.onSurface, fontSize: 26, fontWeight: FontWeight.w700, letterSpacing: -.8))]),
      const SizedBox(height: 46),
      Text('Closer to\nyour field.', style: TextStyle(color: cs.onSurface, fontSize: 44, height: 1.1, fontWeight: FontWeight.w500, letterSpacing: -1.5)),
      const SizedBox(height: 16),
      Text('Sign in to connect cameras and review real monitoring events.', style: TextStyle(color: muted, fontSize: 14, height: 1.7)),
      const SizedBox(height: 30),
      TextFormField(controller: _email, keyboardType: TextInputType.emailAddress, textInputAction: TextInputAction.next, autofillHints: const [AutofillHints.email], decoration: const InputDecoration(labelText: 'Email'), validator: (value) => value != null && value.contains('@') ? null : 'Enter your email address'),
      const SizedBox(height: 16),
      TextFormField(controller: _password, obscureText: _obscure, autofillHints: const [AutofillHints.password], decoration: InputDecoration(labelText: 'Password', suffixIcon: IconButton(tooltip: _obscure ? 'Show password' : 'Hide password', icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined), onPressed: () => setState(() => _obscure = !_obscure))), validator: (value) => value == null || value.isEmpty ? 'Enter your password' : null),
      Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () {
        final email = _email.text.trim();
        if (!email.contains('@')) { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter your email address first.'))); return; }
        context.read<AuthBloc>().add(AuthForgotPasswordRequested(email: email));
      }, child: const Text('Forgot password?'))),
      const SizedBox(height: 8),
      BlocBuilder<AuthBloc, AuthState>(builder: (context, state) => FilledButton(onPressed: state is AuthLoading ? null : () {
        if (_form.currentState!.validate()) context.read<AuthBloc>().add(AuthLoginRequested(email: _email.text.trim(), password: _password.text));
      }, child: state is AuthLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Sign in'))),
      const SizedBox(height: 12),
      Center(child: TextButton(onPressed: () => context.go('/signup'), child: const Text('Create an account'))),
      const SizedBox(height: 26),
      Container(width: double.infinity, padding: const EdgeInsets.all(22), decoration: BoxDecoration(color: cs.surface, borderRadius: BorderRadius.circular(20)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Just checking a leaf?', style: TextStyle(color: cs.onSurface, fontSize: 19, fontWeight: FontWeight.w600)), const SizedBox(height: 8),
        Text('Tomato leaf analysis works on this phone without an account or internet connection.', style: TextStyle(color: muted, height: 1.7, fontSize: 12)), const SizedBox(height: 15),
        OutlinedButton(onPressed: () => context.go('/offline-analysis'), child: const Text('Try offline leaf analysis')),
      ])),
      const SizedBox(height: 24),
    ]))))))));
  }
}
