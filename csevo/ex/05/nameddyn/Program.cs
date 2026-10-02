// 슬라이드 p5-v4-named-dynamic — 동적 호출의 명명 인수, C# 4.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class Image
{
    public string Resize(int w, int height)
    {
        return w + "x" + height;
    }
}

class Program
{
    static void Main()
    {
        dynamic img = new Image();
        Console.WriteLine(img.Resize(height: 480, w: 640));
        try
        {
            Console.WriteLine(img.Resize(width: 640, height: 480));
        }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
