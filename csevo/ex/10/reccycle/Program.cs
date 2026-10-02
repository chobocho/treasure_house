// 슬라이드 p10-v9-rec-cycle — 자기를 가리키는 레코드의 ToString, C# 9.0
using System;

record Node(string Name)
{
    public Node Next { get; set; }
}

class App
{
    static void Main()
    {
        Node a = new Node("a");
        a.Next = new Node("b");
        Console.WriteLine(a);
        a.Next.Next = a;                     // a -> b -> a -> ...
        try
        {
            Console.WriteLine(a.ToString());
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().FullName);
        }
    }
}
