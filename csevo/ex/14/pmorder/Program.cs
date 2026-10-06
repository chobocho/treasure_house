// 슬라이드 p14-v13-pm-order — 컬렉션은 언제 만들어지나, C# 13
using System;
using System.Collections;
using System.Collections.Generic;

class Log : IEnumerable<int>
{
    public Log() => Console.Write("new ");
    public void Add(int x) => Console.Write("Add(" + x + ") ");
    public IEnumerator<int> GetEnumerator() => null;
    IEnumerator IEnumerable.GetEnumerator() => null;
}

class Program
{
    static int Get(string n, int v)
    {
        Console.Write(n + " ");
        return v;
    }

    static void Coll(int a, int b, params Log c) => Console.WriteLine();
    static void Arr(int a, int b, params int[] c) =>
        Console.WriteLine("int[" + c.Length + "]");

    static void Main()
    {
        // the proposal's call: b, then c, then a
        Coll(b: Get("B", 2), c: Get("C", 3), a: Get("A", 1));
        Coll(Get("A", 1), Get("B", 2), Get("C", 3), Get("D", 4));
        Arr(Get("A", 1), Get("B", 2), Get("C", 3), Get("D", 4));
    }
}
