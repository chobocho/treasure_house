// 슬라이드 p5-v4-var-infer — 형식 유추도 변성을 쓴다, C# 4.0
using System;
using System.Collections.Generic;

class Animal { }
class Cat : Animal { }

class Program
{
    static T First<T>(IEnumerable<T> a, IEnumerable<T> b)
    {
        foreach (T x in a) return x;
        foreach (T y in b) return y;
        return default(T);
    }

    static void Main()
    {
        List<Cat> cats = new List<Cat>();
        cats.Add(new Cat());
        List<Animal> animals = new List<Animal>();
        Animal first = First(cats, animals);   // T = Animal
        Console.WriteLine(first.GetType().Name);
    }
}
