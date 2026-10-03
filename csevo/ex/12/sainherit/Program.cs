// 슬라이드 p12-v11-sa-inherit — 클래스 계층과 static 구현, C# 11.0
using System;

interface IKind { static abstract string Kind { get; } }

class Animal : IKind
{
    public static string Kind => "animal";
}

class Cat : Animal { }                       // inherits the static

class Dog : Animal, IKind                    // re-implements
{
    public static new string Kind => "dog";
}

interface IMk<T> where T : IMk<T> { static abstract T Make(); }

class Base : IMk<Base> { public static Base Make() => new Base(); }
class Sub : Base { }

class App
{
    static string K<T>() where T : IKind => T.Kind;
    static string M<T>() where T : IMk<T> => T.Make().GetType().Name;

    static void Main()
    {
        Console.WriteLine(K<Animal>() + " " + K<Cat>() + " "
            + K<Dog>());
        Console.WriteLine(M<Base>());
#if BAD
        Console.WriteLine(M<Sub>());     // Sub is not IMk<Sub>
#endif
    }
}
