// 슬라이드 p10-v9-pat-narrow — and 가 오른쪽 입력을 좁힌다, C# 9.0
using System;

class App
{
    static string Size(object o) => o switch
    {
        byte and < 100 => "small byte",
        byte => "big byte",
        int and (< 0 or > 1000) => "int outside 0..1000",
        int i => "int " + i,
        < 10L => "long under 10",
        _ => "other " + o.GetType().Name,
    };

    static void Main()
    {
        object[] all = { (byte)5, (byte)200, -3, 5000, 7, 7L, 70L };
        foreach (object o in all)
            Console.WriteLine(Size(o));
    }
}
