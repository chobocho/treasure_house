// 슬라이드 p12-v11-rq-inherit — 상속되는 required 목록, C# 11
using System;

class Animal
{
    public required string Name { get; init; }
    public virtual string Sound { get; init; } = "?";
}

class Cat : Animal { }                   // inherits Name's contract

class Dog : Animal                       // adds Sound to the list
{
    public required override string Sound { get; init; }
}

class Base { public virtual required int X { get; set; } }

class Sub : Base
{
#if BAD
    public override int X { get; set; }  // drops 'required'
#else
    public required override int X { get; set; }
#endif
}

class Program
{
    static void Main()
    {
        Console.WriteLine(new Cat { Name = "Tom" }.Sound);
        Console.WriteLine(new Dog { Name = "Rex", Sound = "wo" }.Sound);
        Console.WriteLine(new Sub { X = 3 }.X);
#if BAD2
        Console.WriteLine(new Dog { Name = "Rex" }.Sound);
#endif
    }
}
