// 슬라이드 p8-v7_3-reffor — ref for 와 ref foreach, C# 7.3
using System;

struct Node
{
    public int Value, Next;          // Next: index of the next node
    public Node(int v, int n) { Value = v; Next = n; }
}

class App
{
    static void Main()
    {
        Node[] nodes = { new Node(1, 2), new Node(3, -1),
                         new Node(2, 1) };
        // walk the chain 0 -> 2 -> 1 by reference
        for (ref Node n = ref nodes[0]; ; n = ref nodes[n.Next])
        {
            n.Value *= 10;
            if (n.Next < 0) break;
        }
        foreach (ref Node n in nodes.AsSpan())   // ref foreach
        {
            n.Value += 1;
        }
        foreach (Node n in nodes) Console.Write(n.Value + " ");
        Console.WriteLine();
#if BAD
        foreach (ref Node n in nodes) { }        // an array itself
#endif
    }
}
