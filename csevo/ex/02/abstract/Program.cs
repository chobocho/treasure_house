// 슬라이드 p2-v1-abstract — 추상 클래스와 추상 메서드, C# 1.0
using System;

abstract class Animal
{
    protected string name;
    protected Animal(string name) { this.name = name; }
    public abstract string Sound();                 // no body
    public string Speak() { return name + ": " + Sound(); }
}

class Dog : Animal
{
    public Dog() : base("dog") { }
    public override string Sound() { return "woof"; }
}

class Cat : Animal
{
    public Cat() : base("cat") { }
    public override string Sound() { return "meow"; }
}

class App
{
    static void Main()
    {
        Animal[] zoo = { new Dog(), new Cat() };
        foreach (Animal a in zoo)
            Console.WriteLine(a.Speak());
        Console.WriteLine("abstract: " + typeof(Animal).IsAbstract);
    }
}
