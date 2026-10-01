// 슬라이드 p2-v1-boxmut — 박싱된 구조체를 고치면, C# 1.0
using System;
using System.Collections;

interface ICounter { void Bump(); }

struct Counter : ICounter
{
    public int N;
    public void Bump() { N++; }
}

class App
{
    static void Main()
    {
        ArrayList list = new ArrayList();
        list.Add(new Counter());
        ((Counter)list[0]).Bump();     // bumps an unboxed copy
        Console.WriteLine("via cast:      " + ((Counter)list[0]).N);

        ((ICounter)list[0]).Bump();    // bumps the box itself
        Console.WriteLine("via interface: " + ((Counter)list[0]).N);

        Counter c = new Counter();
        object box = c;                // box holds a copy
        c.Bump();
        Console.WriteLine("local " + c.N + ", box " + ((Counter)box).N);
    }
}
