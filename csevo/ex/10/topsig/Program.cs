// 슬라이드 p10-v9-top-sig — 진입점의 서명은 본문이 정한다, C# 9.0
using System;
using System.Reflection;
using System.Threading.Tasks;

MethodInfo e = Assembly.GetEntryAssembly().EntryPoint;
Console.WriteLine("entry: " + e.ReturnType.Name + " " + e.Name);
BindingFlags f = BindingFlags.Static | BindingFlags.NonPublic;
foreach (MethodInfo m in typeof(Program).GetMethods(f))
    Console.WriteLine("  " + m.ReturnType.Name + " " + m.Name);
#if AWAIT
await Task.Yield();
#endif
#if RET
return 3;
#endif
