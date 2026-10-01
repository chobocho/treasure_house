// 슬라이드 p3-v2-accessor-interface — 인터페이스에 없는 쪽, C# 2.0
using System;

interface INamed
{
    string Name { get; }
}

class User : INamed
{
    string name;
    public string Name
    {
        get { return name; }             // implements INamed.Name
        internal set { name = value; }   // extra, so it may be narrower
    }
}

class App
{
    static void Main()
    {
        User u = new User();
        u.Name = "ada";                  // same assembly: ok
        INamed n = u;
        Console.WriteLine(n.Name);
    }
}
