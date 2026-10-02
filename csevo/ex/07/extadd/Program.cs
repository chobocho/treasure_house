// 슬라이드 p7-v6-extadd — 확장 메서드 Add, C# 6.0
using System;
using System.Collections.Generic;

static class StackExtensions
{
    public static void Add<T>(this Stack<T> s, T item)
    {
        s.Push(item);
    }
}

class Program
{
    static void Main()
    {
        Stack<int> s = new Stack<int> { 1, 2, 3 };    // Push via Add
        Console.WriteLine(s.Pop() + " " + s.Pop() + " " + s.Pop());
    }
}
