// 슬라이드 p5-v4-var-co — 공변: 내보내기만 하는 T, C# 4.0
using System;
using System.Collections.Generic;

class Animal { public virtual string Name { get { return "?"; } } }
class Cat : Animal
{
    public override string Name { get { return "cat"; } }
}

class Program
{
    static void PrintAll(IEnumerable<Animal> animals)
    {
        string line = "";
        foreach (Animal a in animals) line += a.Name + " ";
        Console.WriteLine(line.TrimEnd());
    }

    static void Main()
    {
        List<Cat> cats = new List<Cat>();
        cats.Add(new Cat());
        cats.Add(new Cat());
        PrintAll(cats);                       // IEnumerable<out T>
        Func<Cat> makeCat = delegate { return new Cat(); };
        Func<Animal> makeAnimal = makeCat;    // Func<out TResult>
        Console.WriteLine(makeAnimal().Name);
    }
}
