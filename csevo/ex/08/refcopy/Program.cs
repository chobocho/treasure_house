// 슬라이드 p8-v7-ref-copy — 복사할지 참조할지는 호출자가 정한다, C# 7.0
using System;

class App
{
    static int[] data = { 10, 20, 30 };

    static ref int At(int i)
    {
        return ref data[i];
    }

    static void Main()
    {
        int copy = At(0);          // no 'ref': the value is copied
        ref int alias = ref At(1); // 'ref' on both sides: an alias
        var v = At(2);             // var is int: also a copy
        ref var r = ref At(2);     // ref var is ref int
        copy += 1;
        alias += 1;
        v += 1;
        r += 100;
        Console.WriteLine(string.Join(",", data));
        Console.WriteLine("copy={0} v={1}", copy, v);
    }
}
