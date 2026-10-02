// 슬라이드 p5-v4-var-ext — 확장 메서드의 this 도 변성을 탄다, C# 4.0
using System;
using System.Collections.Generic;

class Animal { public string Name; }
class Cat : Animal { }

static class AnimalExt
{
    public static string Names(this IEnumerable<Animal> all)
    {
        string s = "";
        foreach (Animal a in all) s += a.Name + ";";
        return s;
    }
}

class Program
{
    static void Main()
    {
        List<Cat> cats = new List<Cat>();
        cats.Add(new Cat { Name = "Tom" });
        cats.Add(new Cat { Name = "Kit" });
        Console.WriteLine(cats.Names());    // List<Cat> as receiver
        Cat[] arr = { new Cat { Name = "Arr" } };
        Console.WriteLine(arr.Names());
    }
}
