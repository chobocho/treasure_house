// 슬라이드 p7-v6-nullcond-chain — 사슬 전체를 건너뛴다, C# 6.0
using System;

class Node
{
    public Node Next;
    public string Tag(string s) { return "tag:" + s; }
}

class App
{
    static string Arg(string s)
    {
        Console.WriteLine("  Arg(" + s + ") evaluated");
        return s;
    }

    static void Main()
    {
        Node none = null;
        Node one = new Node();             // one.Next is null
        Node two = new Node { Next = new Node() };

        Console.WriteLine("none: " + none?.Next.Tag(Arg("a")));
        Console.WriteLine("two:  " + two?.Next.Tag(Arg("b")));
        try
        {
            Console.WriteLine("one:  " + one?.Next.Tag(Arg("c")));
        }
        catch (NullReferenceException)
        {
            Console.WriteLine("one:  NullReferenceException");
        }
        Console.WriteLine("one:  " + one?.Next?.Tag(Arg("d")));
    }
}
