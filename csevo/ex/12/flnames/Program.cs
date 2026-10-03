// 슬라이드 p12-v11-fl-names — 쓸 수 없게 된 형식 이름, C# 11
using System;

#if FILE
class file { }
#elif SCOPED
class scoped { }
#elif REQ
class required { }
#else
class @file { }                  // escaped: still the name "file"
#endif

class Program
{
    static void Main()
    {
        foreach (Type t in typeof(Program).Assembly.GetTypes())
            if (t.Namespace == null && t != typeof(Program))
                Console.WriteLine("type: " + t.Name);
    }
}
