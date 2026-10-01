// 슬라이드 p3-v2-arity — 형식 매개변수 수가 다른 같은 이름, C# 2.0
using System;

class Box { }
class Box<T> { }
class Box<T, U> { }

class App
{
    static void Main()
    {
        Console.WriteLine(typeof(Box).Name);
        Console.WriteLine(typeof(Box<>).Name);
        Console.WriteLine(typeof(Box<,>).Name);
        Console.WriteLine(typeof(Box<int>).Name);
        Console.WriteLine(typeof(Box<int, string>));
        Console.WriteLine(typeof(Box<>).IsGenericTypeDefinition);
        Console.WriteLine(typeof(Box<int>).IsGenericTypeDefinition);
    }
}
