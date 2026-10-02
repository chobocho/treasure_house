// 슬라이드 p10-v9-top-main — 컴파일러가 만든 Program 과 <Main>$, C# 9.0
using System;
using System.Reflection;

MethodInfo m = Assembly.GetEntryAssembly().EntryPoint;
Type t = m.DeclaringType;
ParameterInfo p = m.GetParameters()[0];
Console.WriteLine("type      : " + t.FullName);
Console.WriteLine("namespace : " + (t.Namespace ?? "(global)"));
Console.WriteLine("method    : " + m.Name);
Console.WriteLine($"private   : {m.IsPrivate}, static: {m.IsStatic}");
Console.WriteLine("parameter : " + p.ParameterType.Name + " " + p.Name);
Console.WriteLine("returns   : " + m.ReturnType.Name);
Console.WriteLine("same type : " + (t == typeof(Program)));
foreach (CustomAttributeData a in t.GetCustomAttributesData())
    Console.WriteLine("type attr : " + a.AttributeType.Name);
foreach (CustomAttributeData a in m.GetCustomAttributesData())
    Console.WriteLine("main attr : " + a.AttributeType.Name);
