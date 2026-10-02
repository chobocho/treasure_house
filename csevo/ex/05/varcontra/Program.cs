// 슬라이드 p5-v4-var-contra — 반공변: 받기만 하는 T, C# 4.0
using System;
using System.Collections.Generic;

class Animal { public string Name; }
class Cat : Animal { }

class ByName : IComparer<Animal>
{
    public int Compare(Animal x, Animal y)
    {
        return string.CompareOrdinal(x.Name, y.Name);
    }
}

class Program
{
    static void Main()
    {
        List<Cat> cats = new List<Cat>();
        cats.Add(new Cat { Name = "Tom" });
        cats.Add(new Cat { Name = "Felix" });
        IComparer<Cat> cmp = new ByName();     // IComparer<in T>
        cats.Sort(cmp);
        Console.WriteLine(cats[0].Name + ", " + cats[1].Name);

        Action<Animal> pet = delegate(Animal a) {
            Console.WriteLine("pet " + a.Name); };
        Action<Cat> petCat = pet;              // Action<in T>
        petCat(cats[1]);
    }
}
