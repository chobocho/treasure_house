// 슬라이드 p11-v10-pp-eval — 확장 속성 패턴은 몇 번 읽는가, C# 10.0
using System;

class Node
{
    public string Name;
    Node next;
    public Node(string name, Node next = null)
    {
        Name = name;
        this.next = next;
    }
    public Node Next
    {
        get { Console.Write($"[{Name}.Next]"); return next; }
    }
}

class App
{
    static void Main()
    {
        var list = new Node("a", new Node("b", new Node("c")));
        // the same path Next.Next twice, and Next once more
        bool hit = list is { Next.Next.Name: "c", Next.Next.Next: null,
                             Next.Name: "b" };
        Console.WriteLine($" -> {hit}");
        // the nested form of the same test
        hit = list is { Next: { Next: { Name: "c", Next: null },
                                Name: "b" } };
        Console.WriteLine($" -> {hit}");
        var shortList = new Node("a");
        hit = shortList is { Next.Next.Name: "c" };
        Console.WriteLine($" -> {hit}");
    }
}
