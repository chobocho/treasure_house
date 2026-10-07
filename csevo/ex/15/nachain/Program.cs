// 슬라이드 p15-v14-na-chain — 사슬과 겹친 대입, C# 14
using System;

class Node
{
    public string Name;
    public Node Next;
    public string Tag;
    public override string ToString() =>
        (Name ?? "-") + "/" + (Tag ?? "-");
}

class Program
{
    static void Main()
    {
        Node a = new Node { Next = new Node() };
        Node lone = new Node();             // Next is null
        a?.Next?.Name = "n1";               // both links present
        lone?.Next?.Name = "n2";            // stops at lone.Next
        Console.WriteLine(a.Next + " " + lone);

        Node c = new Node(), e = new Node { Tag = "e" }, none = null;
        a?.Tag = c?.Tag = e?.Tag;           // right-associative
        Console.WriteLine(a + " " + c);
        a?.Tag = none?.Tag;                 // assigns null
        Console.WriteLine(a);
    }
}
