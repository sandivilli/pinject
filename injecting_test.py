
import unittest

import errors
import injecting


class InjectorProvideTest(unittest.TestCase):

    def test_can_provide_trivial_class(self):
        class ExampleClassWithInit(object):
            def __init__(self):
                pass
        injector = injecting.NewInjector(classes=[ExampleClassWithInit])
        self.assertTrue(isinstance(injector.provide(ExampleClassWithInit),
                                   ExampleClassWithInit))

    def test_can_provide_class_without_own_init(self):
        class ExampleClassWithoutInit(object):
            pass
        injector = injecting.NewInjector(classes=[ExampleClassWithoutInit])
        self.assertIsInstance(injector.provide(ExampleClassWithoutInit),
                              ExampleClassWithoutInit)

    def test_can_directly_provide_class_with_colliding_arg_name(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        injector = injecting.NewInjector(
            classes=[_CollidingExampleClass, CollidingExampleClass])
        self.assertIsInstance(injector.provide(CollidingExampleClass),
                              CollidingExampleClass)

    def test_can_provide_class_that_itself_requires_injection(self):
        class ClassOne(object):
            def __init__(self, class_two):
                pass
        class ClassTwo(object):
            pass
        injector = injecting.NewInjector(classes=[ClassOne, ClassTwo])
        self.assertIsInstance(injector.provide(ClassOne), ClassOne)

    def test_raises_error_if_arg_is_ambiguously_injectable(self):
        class _CollidingExampleClass(object):
            pass
        class CollidingExampleClass(object):
            pass
        class AmbiguousParamClass(object):
            def __init__(self, colliding_example_class):
                pass
        injector = injecting.NewInjector(
            classes=[_CollidingExampleClass, CollidingExampleClass,
                     AmbiguousParamClass])
        self.assertRaises(errors.AmbiguousArgNameError,
                          injector.provide, AmbiguousParamClass)

    def test_raises_error_if_arg_refers_to_no_known_class(self):
        class UnknownParamClass(object):
            def __init__(self, unknown_class):
                pass
        injector = injecting.NewInjector(classes=[UnknownParamClass])
        self.assertRaises(errors.NothingInjectableForArgNameError,
                          injector.provide, UnknownParamClass)


class InjectorWrapTest(unittest.TestCase):

    def test_can_inject_nothing_into_fn_with_zero_params(self):
        def ReturnSomething():
            return 'something'
        wrapped = injecting.NewInjector(classes=[]).wrap(ReturnSomething)
        self.assertEqual('something', wrapped())

    def test_can_inject_nothing_into_fn_with_positional_passed_params(self):
        def Add(a, b):
            return a + b
        wrapped = injecting.NewInjector(classes=[]).wrap(Add)
        self.assertEqual(5, wrapped(2, 3))

    def test_can_inject_nothing_into_fn_with_keyword_passed_params(self):
        def Add(a, b):
            return a + b
        wrapped = injecting.NewInjector(classes=[]).wrap(Add)
        self.assertEqual(5, wrapped(a=2, b=3))

    def test_can_inject_nothing_into_fn_with_defaults(self):
        def Add(a=2, b=3):
            return a + b
        wrapped = injecting.NewInjector(classes=[]).wrap(Add)
        self.assertEqual(5, wrapped())

    def test_can_inject_nothing_into_fn_with_pargs_and_kwargs(self):
        def Add(*pargs, **kwargs):
            return pargs[0] + kwargs['b']
        wrapped = injecting.NewInjector(classes=[]).wrap(Add)
        self.assertEqual(5, wrapped(2, b=3))

    def test_can_inject_something_into_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.a = 2
        def Add(foo, b):
            return foo.a + b
        wrapped = injecting.NewInjector(classes=[Foo]).wrap(Add)
        self.assertEqual(5, wrapped(b=3))

    def test_can_inject_something_into_non_first_positional_param(self):
        class Foo(object):
            def __init__(self):
                self.b = 3
        def Add(a, foo):
            return a + foo.b
        wrapped = injecting.NewInjector(classes=[Foo]).wrap(Add)
        self.assertEqual(5, wrapped(2))


class InjectorNotYetInstantiatedTest(unittest.TestCase):

    def test_calling_method_raises_error(self):
        injector = injecting._InjectorNotYetInstantiated()
        self.assertRaises(errors.InjectorNotYetInstantiatedError,
                          injector.provide, 'unused-class')


class FutureInjectorTest(unittest.TestCase):

    def test_calling_method_when_injector_not_yet_set_raises_error(self):
        future_injector = injecting._FutureInjector()
        self.assertRaises(errors.InjectorNotYetInstantiatedError,
                          future_injector.provide, 'unused-class')

    def test_calling_method_calls_method_on_contained_injector(self):
        future_injector = injecting._FutureInjector()
        class SomeClass(object):
            pass
        future_injector.set_injector(injecting.NewInjector(classes=[SomeClass]))
        self.assertIsInstance(future_injector.provide(SomeClass), SomeClass)
