
import threading
import unittest

import binding
import errors
import injecting
import scoping
import wrapping


class BindsToTest(unittest.TestCase):

    def test_adds_binding_attrs(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        self.assertTrue(getattr(SomeClass, binding._IS_DECORATED_ATTR))
        self.assertEqual(
            [binding.new_binding_key('foo')],
            getattr(SomeClass, binding._BOUND_TO_BINDING_KEYS_ATTR))

    def test_can_decorate_several_times(self):
        @binding.binds_to('foo', annotated_with='an-annotation')
        @binding.binds_to('bar')
        class SomeClass(object):
            pass
        self.assertEqual(
            [binding.new_binding_key('bar'),
             binding.new_binding_key('foo', 'an-annotation')],
            getattr(SomeClass, binding._BOUND_TO_BINDING_KEYS_ATTR))


class AnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('annotated with "foo"',
                         binding.Annotation('foo').as_adjective())

    def test_equal(self):
        self.assertEqual(binding.Annotation('foo'), binding.Annotation('foo'))
        self.assertEqual(hash(binding.Annotation('foo')),
                         hash(binding.Annotation('foo')))

    def test_not_equal(self):
        self.assertNotEqual(binding.Annotation('foo'),
                            binding.Annotation('bar'))
        self.assertNotEqual(hash(binding.Annotation('foo')),
                            hash(binding.Annotation('bar')))


class NoAnnotationTest(unittest.TestCase):

    def test_as_correct_adjective(self):
        self.assertEqual('unannotated', binding._NoAnnotation().as_adjective())

    def test_equal(self):
        self.assertEqual(binding._NoAnnotation(), binding._NoAnnotation())
        self.assertEqual(hash(binding._NoAnnotation()),
                         hash(binding._NoAnnotation()))

    def test_not_equal(self):
        self.assertNotEqual(binding._NoAnnotation(),
                            binding.Annotation('bar'))
        self.assertNotEqual(hash(binding._NoAnnotation()),
                            hash(binding.Annotation('bar')))


class BindingKeyTest(unittest.TestCase):

    def test_repr(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('an-annotation'))
        self.assertEqual('<the arg name "an-arg-name" annotated with "an-annotation">',
                         repr(binding_key))

    def test_str(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('an-annotation'))
        self.assertEqual('the arg name "an-arg-name" annotated with "an-annotation"',
                         str(binding_key))

    def test_equal_if_same_arg_name_and_annotation(self):
        binding_key_one = binding.BindingKey(
            'an-arg-name', binding.Annotation('an-annotation'))
        binding_key_two = binding.BindingKey(
            'an-arg-name', binding.Annotation('an-annotation'))
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding.BindingKey(
            'arg-name-one', binding.Annotation('an-annotation'))
        binding_key_two = binding.BindingKey(
            'arg-name-two', binding.Annotation('an-annotation'))
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_annotation(self):
        binding_key_one = binding.BindingKey(
            'arg-name-one', binding.Annotation('an-annotation'))
        binding_key_two = binding.BindingKey(
            'arg-name-two', binding.Annotation('another-annotation'))
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_can_apply_to_one_of_arg_names(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('unused'))
        self.assertTrue(binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'an-arg-name', 'bar']))

    def test_cannot_apply_to_one_of_arg_names(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('unused'))
        self.assertFalse(binding_key.can_apply_to_one_of_arg_names(
            ['foo', 'other-arg-name', 'bar']))

    def test_conflicts_with_some_binding_key(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('ann1'))
        non_conflicting_binding_key = binding.BindingKey(
            'other-arg-name', binding.Annotation('unused'))
        conflicting_binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('ann2'))
        self.assertTrue(binding_key.conflicts_with_any_binding_key(
            [non_conflicting_binding_key, conflicting_binding_key]))

    def test_doesnt_conflict_with_any_binding_key(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('ann1'))
        non_conflicting_binding_key = binding.BindingKey(
            'other-arg-name', binding.Annotation('unused'))
        self.assertFalse(binding_key.conflicts_with_any_binding_key(
            [non_conflicting_binding_key]))

    def test_puts_provided_value_in_kwargs(self):
        binding_key = binding.BindingKey(
            'an-arg-name', binding.Annotation('unused'))
        kwargs = {}
        binding_key.put_provided_value_in_kwargs('a-value', kwargs)
        self.assertEqual({'an-arg-name': 'a-value'}, kwargs)


class GetUnboundArgNamesTest(unittest.TestCase):

    def test_all_arg_names_bound(self):
        arg_names = ['bound1', 'bound2']
        binding_keys = [binding.new_binding_key('bound1'),
                        binding.new_binding_key('bound2')]
        self.assertEqual(
            [], binding.get_unbound_arg_names(arg_names, binding_keys))

    def test_some_arg_name_unbound(self):
        arg_names = ['bound', 'unbound']
        binding_keys = [binding.new_binding_key('bound')]
        self.assertEqual(
            ['unbound'], binding.get_unbound_arg_names(arg_names, binding_keys))


class NewBindingKeyTest(unittest.TestCase):

    def test_without_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name')
        self.assertEqual('the arg name "an-arg-name" unannotated', str(binding_key))

    def test_with_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name', 'an-annotation')
        self.assertEqual('the arg name "an-arg-name" annotated with "an-annotation"',
                         str(binding_key))


class GetBindingKeyToBindingMapsTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding.new_binding_key('some_class')
        self.some_binding = binding.Binding(
            self.some_binding_key, 'a-proviser-fn')
        self.another_some_binding = binding.Binding(
            self.some_binding_key, 'another-proviser-fn')

    def assertBindingsReturnMaps(
            self, bindings, binding_key_to_binding,
            collided_binding_key_to_bindings,
            handle_binding_collision_fn='unused-handle-binding-collision'):
        self.assertEqual(
            (binding_key_to_binding, collided_binding_key_to_bindings),
            binding._get_binding_key_to_binding_maps(
                bindings, handle_binding_collision_fn))

    def assertBindingsRaise(
            self, bindings, error_type,
            handle_binding_collision_fn='unused-handle-binding-collision'):
        self.assertRaises(error_type,
                          binding._get_binding_key_to_binding_maps,
                          bindings, handle_binding_collision_fn)

    def test_no_input_bindings_returns_empty_maps(self):
        self.assertBindingsReturnMaps(
            bindings=[],
            binding_key_to_binding={}, collided_binding_key_to_bindings={})

    def test_single_binding_gets_returned(self):
        self.assertBindingsReturnMaps(
            bindings=[self.some_binding],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_colliding_classes_calls_handler(self):
        was_called = threading.Event()
        def handle_binding_collision_fn(colliding_binding, binding_key_to_binding,
                                        collided_binding_key_to_bindings):
            binding_key = colliding_binding.binding_key
            self.assertEqual(self.another_some_binding.binding_key, binding_key)
            self.assertEqual({self.some_binding_key: self.some_binding},
                             binding_key_to_binding)
            self.assertEqual({}, collided_binding_key_to_bindings)
            was_called.set()
        self.assertBindingsReturnMaps(
            bindings=[self.some_binding, self.another_some_binding],
            handle_binding_collision_fn=handle_binding_collision_fn,
            binding_key_to_binding={self.some_binding_key: self.another_some_binding},
            collided_binding_key_to_bindings={})
        self.assertTrue(was_called.is_set())


class GetOverallBindingKeyToBindingMapsTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding.new_binding_key('some_class')
        self.some_binding = binding.Binding(
            self.some_binding_key, 'a-proviser-fn')
        self.another_some_binding = binding.Binding(
            self.some_binding_key, 'another-proviser-fn')

    def assertBindingsListsReturnMaps(
            self, bindings_lists,
            binding_key_to_binding, collided_binding_key_to_bindings):
        self.assertEqual(
            (binding_key_to_binding, collided_binding_key_to_bindings),
            binding.get_overall_binding_key_to_binding_maps(bindings_lists))

    def assertBindingsListsRaise(self, bindings_lists, error_type):
        self.assertRaises(error_type,
                          binding.get_overall_binding_key_to_binding_maps,
                          bindings_lists)

    def test_no_input_bindings_returns_empty_maps(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[],
            binding_key_to_binding={}, collided_binding_key_to_bindings={})

    def test_single_binding_gets_returned(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_higher_priority_binding_overrides_lower(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.another_some_binding], [self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_higher_priority_binding_removes_collided_lower_priority(self):
        self.assertBindingsListsReturnMaps(
            bindings_lists=[[self.some_binding, self.another_some_binding],
                            [self.some_binding]],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_colliding_highest_priority_bindings_raises_error(self):
        self.assertBindingsListsRaise(
            bindings_lists=[[self.some_binding, self.another_some_binding]],
            error_type=errors.ConflictingBindingsError)


class BindingMappingTest(unittest.TestCase):

    def test_success(self):
        binding_mapping = binding.BindingMapping(
            {'a-binding-key': 'a-binding'}, {})
        self.assertEqual('a-binding',
                         binding_mapping.get('a-binding-key'))

    def test_unknown_binding_raises_error(self):
        binding_mapping = binding.BindingMapping(
            {'a-binding-key': 'a-binding'}, {})
        self.assertRaises(errors.NothingInjectableForArgError,
                          binding_mapping.get, 'unknown-binding-key')

    def test_colliding_bindings_raises_error(self):
        binding_key = binding.new_binding_key('unused')
        binding_one = binding.Binding(
            binding_key,
            binding.create_proviser_fn(binding_key, to_instance='unused'))
        binding_two = binding.Binding(
            binding_key,
            binding.create_proviser_fn(binding_key, to_instance='unused'))
        binding_mapping = binding.BindingMapping(
            {}, {'colliding-binding-key': [binding_one, binding_two]})
        self.assertRaises(errors.AmbiguousArgNameError,
                          binding_mapping.get, 'colliding-binding-key')


class BindingContextTest(unittest.TestCase):

    def setUp(self):
        self.binding_key = binding.new_binding_key('foo')
        self.binding_context = binding.BindingContext(
            [self.binding_key], 'curr-scope')

    def test_get_child_successfully(self):
        other_binding_key = binding.new_binding_key('bar')
        new_binding_context = self.binding_context.get_child(
            other_binding_key, 'new-scope')
        self.assertTrue(
            new_binding_context.does_scope_id_match(lambda s: s == 'new-scope'))

    def test_get_child_raises_error_when_binding_key_already_seen(self):
        self.assertRaises(
            errors.CyclicInjectionError, self.binding_context.get_child,
            self.binding_key, 'new-scope')

    def test_scope_id_does_match(self):
        self.assertTrue(
            self.binding_context.does_scope_id_match(lambda s: s == 'curr-scope'))

    def test_scope_id_does_not_match(self):
        self.assertFalse(
            self.binding_context.does_scope_id_match(lambda s: s == 'other-scope'))


class DefaultGetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(['foo_bar_baz'], binding.default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual([], binding.default_get_arg_names_from_class_name('notAllCamelCase'))


class FakeInjector(object):

    def provide(self, cls):
        return self._provide_class(cls, _UNUSED_BINDING_CONTEXT)

    def _provide_class(self, cls, binding_context):
        return 'a-provided-{0}'.format(cls.__name__)

    def _call_with_injection(self, provider_fn, binding_context):
        return provider_fn()


_UNUSED_BINDING_CONTEXT = binding.BindingContext('unused', 'unused')
def call_provisor_fn(a_binding):
    return a_binding.proviser_fn(_UNUSED_BINDING_CONTEXT, FakeInjector())


class GetExplicitBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_explicit_bindings([], [], []))

    def test_returns_binding_for_input_explicitly_bound_class(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        [explicit_binding] = binding.get_explicit_bindings(
            [SomeClass], [], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.new_binding_key('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_input_explicitly_injected_class(self):
        class SomeClass(object):
            @wrapping.inject
            def __init__(self):
                pass
        [explicit_binding] = binding.get_explicit_bindings(
            [SomeClass], [], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.new_binding_key('some_class'),
                         explicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_input_provider_fn(self):
        @wrapping.provides('foo')
        def some_function():
            return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [], [some_function], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.new_binding_key('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_provider_fn_on_input_class(self):
        class SomeClass(object):
            @staticmethod
            @wrapping.provides('foo')
            # TODO(kurts): figure out why the decorator order cannot be reversed.
            def some_function():
                return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [SomeClass], [], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.new_binding_key('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))

    def test_returns_binding_in_known_scope(self):
        @wrapping.provides('foo', in_scope='a-scope')
        def some_function():
            return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [], [some_function], scope_ids=['a-scope'])
        self.assertEqual('a-scope', explicit_binding.scope_id)

    def test_raises_error_for_binding_in_unknown_scope(self):
        @wrapping.provides('foo', in_scope='unknown-scope')
        def some_function():
            return 'a-foo'
        self.assertRaises(errors.UnknownScopeError,
                          binding.get_explicit_bindings,
                          [], [some_function], scope_ids=['known-scope'])


class GetImplicitProviderBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_implicit_provider_bindings([], []))

    def test_returns_binding_for_input_provider_fn(self):
        def new_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_provider_bindings(
            classes=[], functions=[new_foo])
        self.assertEqual(binding.new_binding_key('foo'),
                         implicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(implicit_binding))

    def test_returns_no_binding_for_explicit_provider_fn(self):
        @wrapping.provides('bar')
        def new_foo():
            return 'a-foo'
        self.assertEqual(
            [], binding.get_implicit_provider_bindings(classes=[], functions=[new_foo]))

    def test_returns_binding_for_staticmethod_provider_fn(self):
        class SomeClass(object):
            @staticmethod
            def new_foo():
                return 'a-foo'
        [implicit_binding] = binding.get_implicit_provider_bindings(
            classes=[SomeClass], functions=[])
        self.assertEqual(binding.new_binding_key('foo'),
                         implicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(implicit_binding))

    def test_returns_no_binding_for_input_non_provider_fn(self):
        def some_fn():
            pass
        self.assertEqual([], binding.get_implicit_provider_bindings(
            classes=[], functions=[some_fn]))

    def test_uses_provided_fn_to_map_provider_fn_names_to_arg_names(self):
        def some_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_provider_bindings(
            classes=[], functions=[some_foo],
            get_arg_names_from_provider_fn_name=lambda _: ['foo'])
        self.assertEqual(binding.new_binding_key('foo'),
                         implicit_binding.binding_key)


class GetImplicitClassBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_implicit_class_bindings([]))

    def test_returns_binding_for_input_class(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_class_bindings([SomeClass])
        self.assertEqual(binding.new_binding_key('some_class'),
                         implicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(implicit_binding))

    def test_returns_no_binding_for_explicitly_bound_class(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        self.assertEqual([], binding.get_implicit_class_bindings([SomeClass]))

    def test_returns_binding_for_correct_input_class(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        implicit_bindings = binding.get_implicit_class_bindings(
            [ClassOne, ClassTwo])
        for implicit_binding in implicit_bindings:
            if (implicit_binding.binding_key ==
                binding.new_binding_key('class_one')):
                self.assertEqual(
                    'a-provided-ClassOne', call_provisor_fn(implicit_binding))
            else:
                self.assertEqual(implicit_binding.binding_key,
                                 binding.new_binding_key('class_two'))
                self.assertEqual(
                    'a-provided-ClassTwo', call_provisor_fn(implicit_binding))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_class_bindings(
            [SomeClass], get_arg_names_from_class_name=lambda _: ['foo'])
        self.assertEqual(binding.new_binding_key('foo'),
                         implicit_binding.binding_key)


class BinderTest(unittest.TestCase):

    def setUp(self):
        self.collected_bindings = []
        self.binder = binding.Binder(
            self.collected_bindings,
            scope_ids=[scoping.PROTOTYPE, 'known-scope'])

    def test_can_bind_to_class(self):
        class SomeClass(object):
            pass
        self.binder.bind('an-arg-name', to_class=SomeClass)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.new_binding_key('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(only_binding))

    def test_can_bind_to_instance(self):
        an_instance = object()
        self.binder.bind('an-arg-name', to_instance=an_instance)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.new_binding_key('an-arg-name'),
                         only_binding.binding_key)
        self.assertIs(an_instance, call_provisor_fn(only_binding))

    def test_can_bind_to_provider(self):
        self.binder.bind('an-arg-name', to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.new_binding_key('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_can_bind_with_annotation(self):
        self.binder.bind('an-arg-name', annotated_with='an-annotation',
                         to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(
            binding.new_binding_key('an-arg-name', 'an-annotation'),
            only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_can_bind_with_scope(self):
        self.binder.bind('an-arg-name', to_provider=lambda: 'a-provided-thing',
                         in_scope='known-scope')
        [only_binding] = self.collected_bindings
        self.assertEqual('known-scope', only_binding.scope_id)

    def test_binding_to_unknown_scope_raises_error(self):
        self.assertRaises(
            errors.UnknownScopeError, self.binder.bind, 'unused-arg-name',
            to_instance='unused-instance', in_scope='unknown-scope')

    def test_binding_to_nothing_raises_error(self):
        self.assertRaises(errors.NoBindingTargetError,
                          self.binder.bind, 'unused-arg-name')

    def test_binding_to_multiple_things_raises_error(self):
        self.assertRaises(errors.MultipleBindingTargetsError,
                          self.binder.bind, 'unused-arg-name',
                          to_instance=object(), to_provider=lambda: None)

    def test_binding_to_non_class_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_class='not-a-class')

    def test_binding_to_non_provider_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_provider='not-a-provider')
