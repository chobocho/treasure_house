// 슬라이드 p5-v4-var-later — 뒤 버전: 공변 반환 형식, C# 9.0
using System;

class Animal
{
    public virtual Animal Clone() { return new Animal(); }
}

class Cat : Animal
{
    public override Cat Clone() { return new Cat(); }   // narrower
}

class Program
{
    static void Main()
    {
        Cat c = new Cat().Clone();        // no cast needed
        Animal a = c;
        Console.WriteLine(c.GetType().Name + " "
                          + a.Clone().GetType().Name);
    }
}
