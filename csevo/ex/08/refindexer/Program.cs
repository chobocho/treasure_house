// 슬라이드 p8-v7-ref-indexer — ref 를 돌려주는 인덱서와 속성, C# 7.0
using System;

class Buffer
{
    int[] data = new int[4];

    public ref int this[int i] { get { return ref data[i]; } }
    public ref int First { get { return ref data[0]; } }
#if BAD
    public ref int Last
    {
        get { return ref data[3]; }
        set { }
    }
#endif

    public override string ToString()
    {
        return string.Join(",", data);
    }
}

class App
{
    static void Main()
    {
        var b = new Buffer();
        b[1] = 5;                // no setter: assigns through the ref
        b[2]++;
        b.First = 9;
        ref int last = ref b[3];
        last = 4;
        Console.WriteLine(b);
    }
}
