// 슬라이드 p4-v3-implarray-fail — 공통 형식이 없으면, C# 3.0
using System;

class Animal { }
class Dog : Animal { }
class Cat : Animal { }

class App
{
    static void Main()
    {
        object a = new[] { 1, "one" };
        object b = new[] { null, null };
        object c = new[] { new Dog(), new Cat() };
        object d = new Animal[] { new Dog(), new Cat() };   // fine
        Console.WriteLine(d);
    }
}
