// 슬라이드 p12-v11-sa-call — 형식 매개변수로만 부른다, C# 11.0
using System;

interface IName<TSelf> where TSelf : IName<TSelf>
{
    static abstract string Name { get; }
    static abstract TSelf Make();
}

class Cat : IName<Cat>
{
    public static string Name => "Cat";
    public static Cat Make() => new Cat();
}

class Dog : IName<Dog>
{
    static string IName<Dog>.Name => "Dog";      // explicit
    static Dog IName<Dog>.Make() => new Dog();
}

class App
{
    static string Hello<T>() where T : IName<T> =>
        T.Name + " " + T.Make().GetType().Name;

    static void Main()
    {
        Console.WriteLine(Hello<Cat>() + " / " + Hello<Dog>());
        Console.WriteLine(Cat.Name);                 // implicit: public
#if BAD
        Console.WriteLine(IName<Cat>.Name);          // no type argument
#endif
#if BAD2
        Console.WriteLine(Dog.Name);                 // explicit: hidden
#endif
    }
}
