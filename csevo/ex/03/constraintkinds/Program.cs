// 슬라이드 p3-v2-constraint-kinds — 제약의 종류, C# 2.0
using System;
using System.Collections.Generic;

class Animal { public virtual string Name() { return "animal"; } }
class Dog : Animal { public override string Name() { return "dog"; } }

class App
{
    static bool IsNull<T>(T x) where T : class { return x == null; }
    static T? Wrap<T>(T x) where T : struct { return x; }
    static T Fresh<T>() where T : new() { return new T(); }
    static string Call<T>(T a) where T : Animal { return a.Name(); }

    static void Copy<T, U>(List<T> src, List<U> dst) where T : U
    {
        foreach (T x in src)
        {
            dst.Add(x);                   // T converts to U
        }
    }

    static void Main()
    {
        Console.WriteLine(IsNull<string>(null));
        Console.WriteLine(Wrap(5).HasValue);
        Console.WriteLine(Fresh<List<int>>().Count);
        Console.WriteLine(Call(new Dog()));
        List<Dog> dogs = new List<Dog>();
        dogs.Add(new Dog());
        List<Animal> all = new List<Animal>();
        Copy(dogs, all);                  // T = Dog, U = Animal
        Console.WriteLine(all.Count + " " + all[0].Name());
    }
}
