import pygame
import OpenGL
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_limb(j1, j2, j3, j4):
	glBegin(GL_LINE_STRIP)
	glVertex3fv(j1)
	glVertex3fv(j2)
	glVertex3fv(j3)
	glVertex3fv(j4)
	glEnd()

def draw_circle(c_x, c_y, r):
	num_lines = 100

	glBegin(GL_LINE_LOOP)
	for i in range(num_lines):
		glVertex2f(c_x + (r * np.cos(i * 2 * np.pi / num_lines)), 
			    c_y + (r * np.sin(i * 2 * np.pi / num_lines)))
	glEnd()

def draw_point(c_v):
	glBegin(GL_POINTS)
	glVertex3fv(c_v)
	glEnd()

def update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3):
	j2_v = [np.cos(j1_a) * arc1, np.sin(j1_a) * arc1,0] + j1_v
	j2_effective_angle = j2_a + j1_a
	j3_v = [np.cos(j2_effective_angle) * arc2, np.sin(j2_effective_angle) * arc2,0] + j2_v
	j3_effective_angle = j2_effective_angle + j3_a
	j4_v = [np.cos(j3_effective_angle) * arc3, np.sin(j3_effective_angle) * arc3,0] + j3_v
	return j1_v, j2_v, j3_v, j4_v

def compute_angle_once(joint, end, target):
	r = end - joint
	r = r/np.sqrt(r[0]**2 + r[1]**2)
	t = target - joint
	t = t/np.sqrt(t[0]**2 + t[1]**2)
	print("Target = ", t, "End: ", r)
	theta = np.arccos(np.dot(r, t))
	#print("Theta = ", theta)
	return theta

def compute_angle_changes(j1_v, j1_a, j2_v, j2_a, j3_v, j3_a, j4_v, arc1, arc2, arc3, target_point):
	error_v = target_point - j4_v
	error = np.sqrt(error_v[0]**2 + error_v[1]**2 + error_v[2]**2)
	while(error > 0.001):
		j3_c = compute_angle_once(j3_v, j4_v, target_point)
		j3_a += j3_c
		j1_v, j2_v, j3_v, j4_v = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
		error_v = target_point - j4_v
		j2_c = compute_angle_once(j2_v, j4_v, target_point)
		j2_a += j2_c
		j1_v, j2_v, j3_v, j4_v = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
		error_v = target_point - j4_v
		j1_c = compute_angle_once(j1_v, j4_v, target_point)
		j1_a += j1_c
		j1_v, j2_v, j3_v, j4_v = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
		error_v = target_point - j4_v
		error = np.sqrt(error_v[0]**2 + error_v[1]**2 + error_v[2]**2)
		if(j3_c == 0 and j2_c == 0 and j1_c == 0):
			error = 0
		pass
	return j1_a % (np.pi * 2), j2_a % (np.pi * 2), j3_a % (np.pi * 2)

def compute_angle_direction(change):
	if(change > np.pi):
		direction = -1
		angle = np.pi - (np.fabs(change) % np.pi)
	elif(change > 0):
		direction = 1
		angle = np.fabs(change)
	elif(change > -np.pi):
		direction = -1
		angle = np.fabs(change)
	else:
		direction = 1
		angle = np.pi - (np.fabs(change) % np.pi)
	return direction, angle


def main():
	win_height, win_width = 1600,1200

	j1_v = np.array([0,0,0])
	j1_a = 0
	j2_v = np.array([0,0,0])
	arc1 = 8
	j2_a = 0
	arc2 = 7
	j3_v = np.array([0,0,0])
	arc3 = 2
	j3_a = 0
	target_point = np.array([18,0,0])
	turn_speed = np.pi/128

	pygame.init()
	display = (win_height,win_width)
	pygame.display.set_mode(display, DOUBLEBUF|OPENGL)


	gluPerspective(90, display[0]/display[1], 0.1, 50.0)

	glTranslatef(0.0,0.0, -30)

	glRotatef(0,0,0,0)

	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
	j1,j2,j3,j4 = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
	draw_limb(j1,j2,j3,j4)
	draw_circle(j1[0],j1[1], arc1 + arc2 + arc3)
	draw_circle(j2[0],j2[1], arc2 + arc3)
	draw_circle(j3[0],j3[1], arc3)
	draw_point(target_point)
	pygame.display.flip()
	pygame.time.wait(10)

	while True:
		for event in pygame.event.get():
			if(event.type == pygame.QUIT):
				pygame.quit()
				quit()
			if(event.type == pygame.MOUSEBUTTONDOWN):
				target_point = np.append(event.pos, 0)
				#Translate the point from pygame into the coordinate space for opengl
				target_point -= np.array([win_height/2,win_width/2,0]).astype(int)
				target_point = target_point/20
				target_point[1] = target_point[1] * -1
				print(target_point)
		j1,j2,j3,j4 = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
		j1_a_new, j2_a_new, j3_a_new = compute_angle_changes(j1, j1_a, j2, j2_a, j3, j3_a, j4, arc1, arc2, arc3, target_point)
		j1_a_d, j1_a_c = compute_angle_direction(j1_a_new - j1_a) 
		j2_a_d, j2_a_c = compute_angle_direction(j2_a_new - j2_a) 
		j3_a_d, j3_a_c = compute_angle_direction(j3_a_new - j3_a) 
		while(j1_a_c > 0 or j2_a_c > 0 or j3_a_c > 0):
			if(turn_speed < j1_a_c):
				j1_a += turn_speed * j1_a_d
				j1_a_c -= turn_speed
			else:
				j1_a += j1_a_c * j1_a_d
				j1_a_c = 0

			if(turn_speed < j2_a_c):
				j2_a += turn_speed * j2_a_d
				j2_a_c -= turn_speed
			else:
				j2_a += j2_a_c * j2_a_d
				j2_a_c = 0

			if(turn_speed < j3_a_c):
				j3_a += turn_speed * j3_a_d
				j3_a_c -= turn_speed
			else:
				j3_a += j3_a_c * j3_a_d
				j3_a_c = 0

			j1_a, j2_a, j3_a = j1_a % (np.pi * 2), j2_a % (np.pi * 2), j3_a % (np.pi * 2)
			glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
			j1,j2,j3,j4 = update_joints(j1_v, j1_a, j2_a, j3_a, arc1, arc2, arc3)
			draw_limb(j1,j2,j3,j4)
			draw_circle(j1[0],j1[1], arc1 + arc2 + arc3)
			draw_circle(j2[0],j2[1], arc2 + arc3)
			draw_circle(j3[0],j3[1], arc3)
			draw_point(target_point)
			print("End point: ", j4, "Target: ", target_point)
			pygame.display.flip()
			pygame.time.wait(10)
			pass

main()