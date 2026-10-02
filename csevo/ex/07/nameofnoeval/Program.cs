// 슬라이드 p7-v6-nameof-noeval — 피연산자는 평가하지 않는다, C# 6.0
using System;

class Node
{
    public Node Next = null;
    public string Value = null;
}

class App
{
    static int calls;
    static Node Get() { calls++; return null; }

    static void Main()
    {
        Node empty = null;
        string unassigned;                       // never assigned
        Console.WriteLine(nameof(empty.Next.Next.Value));  // no NRE
        Console.WriteLine(nameof(unassigned));   // no CS0165
        Console.WriteLine(nameof(Node.Next.Value));
        Console.WriteLine("calls = " + calls);
    }
}
