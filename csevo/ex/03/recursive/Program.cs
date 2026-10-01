// 슬라이드 p3-v2-iterator-recursive — 반복기 안의 반복기, C# 2.0
using System;
using System.Collections.Generic;

class Node
{
    public readonly int Value;
    public readonly Node Next;
    public Node(int value, Node next) { Value = value; Next = next; }
}

class App
{
    static long moves;                    // values handed up one level

    static IEnumerable<int> Walk(Node n)
    {
        if (n == null) yield break;
        moves++;
        yield return n.Value;
        foreach (int x in Walk(n.Next))   // re-yield the whole tail
        {
            moves++;
            yield return x;
        }
    }

    static void Main()
    {
        int[] sizes = new int[] { 10, 100, 1000 };
        foreach (int size in sizes)
        {
            Node head = null;
            for (int i = 0; i < size; i++) head = new Node(i, head);
            moves = 0;
            foreach (int x in Walk(head)) { }
            Console.WriteLine(size + " nodes: " + moves + " moves");
        }
    }
}
